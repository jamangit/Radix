import asyncio
import contextlib
import json
import logging
import uuid
from collections.abc import Callable
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, Query, WebSocket, status
from pydantic import BaseModel, ValidationError
from sqlalchemy.orm import Session
from starlette.websockets import WebSocketDisconnect

from wordmeter_api.analysis import Language, analyze_detailed
from wordmeter_api.analysis.tokenizer import tokenize
from wordmeter_api.config import settings
from wordmeter_api.db.models import User
from wordmeter_api.dependencies import SessionDep
from wordmeter_api.security import decode_ws_ticket
from wordmeter_api.services.persistence import save_analysis
from wordmeter_api.speech.quality import measure_quality
from wordmeter_api.speech.segmenter import (
    BYTES_PER_SECOND,
    SegmenterConfig,
    UtteranceSegmenter,
    VoiceDetector,
)
from wordmeter_api.speech.transcriber import Transcription, transcribe_pcm
from wordmeter_api.speech.vad import create_voice_detector

logger = logging.getLogger(__name__)
router = APIRouter(tags=["speech"])

MAX_FRAME_BYTES = 64 * 1024
MAX_PENDING_PHRASES = 10
LOCK_CONFIDENCE = 0.8  # in auto mode, the language is locked once Whisper is this sure

PcmTranscriber = Callable[[bytes, str | None], Transcription]
VadFactory = Callable[[], VoiceDetector]


def get_pcm_transcriber() -> PcmTranscriber:
    return transcribe_pcm


def get_vad_factory() -> VadFactory:
    return create_voice_detector


PcmTranscriberDep = Annotated[PcmTranscriber, Depends(get_pcm_transcriber)]
VadFactoryDep = Annotated[VadFactory, Depends(get_vad_factory)]


class StartMessage(BaseModel):
    type: Literal["start"]
    language: Language | None = None  # None means auto-detect


def _as_supported(code: str) -> Language | None:
    if code == "fr":
        return "fr"
    if code == "en":
        return "en"
    return None


class LiveSession:
    """State of one live recording: audio in, phrases out, running word count."""

    def __init__(
        self,
        websocket: WebSocket,
        transcriber: PcmTranscriber,
        detector: VoiceDetector,
        language: Language | None,
    ) -> None:
        self.language = language
        self.overloaded = False
        self._websocket = websocket
        self._transcriber = transcriber
        self._segmenter = UtteranceSegmenter(
            detector, SegmenterConfig(min_silence_ms=settings.vad_silence_ms)
        )
        self._queue: asyncio.Queue[bytes | None] = asyncio.Queue(maxsize=MAX_PENDING_PHRASES)
        self._parts: list[str] = []
        self._total_words = 0
        self._audio_bytes = 0
        self._speaking = False
        self._last_detected: Language | None = None

    async def send(self, payload: dict[str, Any]) -> None:
        # The client may already be gone: results are still saved, so never fail on a send.
        with contextlib.suppress(WebSocketDisconnect, RuntimeError, OSError):
            await self._websocket.send_json(payload)

    async def fail(self, code: str, message: str) -> None:
        await self.send({"type": "error", "code": code, "message": message})

    async def feed(self, pcm: bytes) -> bool:
        """Handle one audio frame. Returns False when the recording must stop."""
        if len(pcm) > MAX_FRAME_BYTES:
            await self.fail("bad_request", "Audio frame too large")
            return False
        self._audio_bytes += len(pcm)
        if self._audio_bytes > settings.max_stream_seconds * BYTES_PER_SECOND:
            await self.fail("too_long", "Maximum recording length reached")
            return False

        phrases = self._segmenter.feed(pcm)
        await self._report_speech_state()
        for phrase in phrases:
            if not await self._enqueue(phrase):
                return False
        return True

    async def _enqueue(self, phrase: bytes) -> bool:
        try:
            self._queue.put_nowait(phrase)
        except asyncio.QueueFull:
            self.overloaded = True
            await self.fail("too_slow", "The server cannot keep up with this recording")
            return False
        return True

    async def _report_speech_state(self) -> None:
        active = self._segmenter.in_speech
        if active != self._speaking:
            self._speaking = active
            await self.send({"type": "speech", "active": active})

    async def finish_input(self) -> None:
        """No more audio: queue the phrase in progress, then tell the worker to stop."""
        last = self._segmenter.flush()
        if last is not None:
            await self._queue.put(last)
        await self._queue.put(None)

    async def run(self) -> None:
        """Worker: transcribe phrases one at a time, in order."""
        while (phrase := await self._queue.get()) is not None:
            await self._transcribe(phrase)

    def _measure(self, pcm: bytes) -> dict[str, Any]:
        quality = measure_quality(
            pcm,
            min_level_db=settings.quality_min_level_db,
            min_snr_db=settings.quality_min_snr_db,
        )
        return {
            "level_db": quality.level_db,
            "snr_db": quality.snr_db,
            "verdict": quality.verdict,
        }

    async def _transcribe(self, pcm: bytes) -> None:
        try:
            transcription = await asyncio.to_thread(self._transcriber, pcm, self.language)
        except Exception:
            logger.exception("Live transcription failed")
            await self.fail("transcription_failed", "Could not transcribe this part")
            return

        quality = self._measure(pcm)
        if not transcription.text:
            # Heard as speech but nothing intelligible came out: often a faint or noisy signal.
            await self.send({"type": "unclear", "quality": quality})
            return

        if self.language is None:
            detected = _as_supported(transcription.language)
            if detected is None:
                await self.fail("unsupported_language", "Only French and English are supported")
                return
            self._last_detected = detected
            if transcription.language_probability >= LOCK_CONFIDENCE:
                self.language = detected

        words = len(tokenize(transcription.text))
        if words == 0:
            return
        self._parts.append(transcription.text)
        self._total_words += words
        await self.send(
            {
                "type": "segment",
                "text": transcription.text,
                "words": words,
                "total_words": self._total_words,
                "quality": quality,
            }
        )

    async def conclude(self, session: Session, user_id: uuid.UUID) -> None:
        """Analyze everything that was said, save it for the recaps, and report."""
        transcript = " ".join(self._parts)
        if not transcript:
            await self.fail("no_speech", "No speech detected")
            return
        language = self.language or self._last_detected or "fr"
        result, counts = await asyncio.to_thread(analyze_detailed, transcript, language)
        await asyncio.to_thread(save_analysis, session, user_id, result, counts)
        await self.send(
            {
                "type": "final",
                **result.model_dump(),
                "transcript": transcript,
                "audio_seconds": round(self._audio_bytes / BYTES_PER_SECOND, 1),
            }
        )


async def _authenticate(session: Session, ticket: str) -> uuid.UUID | None:
    subject = decode_ws_ticket(ticket)
    if subject is None:
        return None
    try:
        user_id = uuid.UUID(subject)
    except ValueError:
        return None
    user = await asyncio.to_thread(session.get, User, user_id)
    return user_id if user is not None else None


def _is_stop(text: str | None) -> bool:
    if text is None:
        return False
    try:
        message = json.loads(text)
    except json.JSONDecodeError:
        return False
    return isinstance(message, dict) and message.get("type") == "stop"


async def _receive_audio(websocket: WebSocket, live: LiveSession) -> None:
    """Read frames until the client stops, disconnects, or breaks a limit."""
    while True:
        message = await websocket.receive()
        if message["type"] == "websocket.disconnect":
            return
        data = message.get("bytes")
        if data is not None:
            if not await live.feed(data):
                return
        elif _is_stop(message.get("text")):
            return


@router.websocket("/ws/transcribe")
async def live_transcription(
    websocket: WebSocket,
    session: SessionDep,
    transcriber: PcmTranscriberDep,
    vad_factory: VadFactoryDep,
    ticket: Annotated[str, Query()] = "",
) -> None:
    user_id = await _authenticate(session, ticket)
    if user_id is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    await websocket.accept()

    try:
        start = StartMessage.model_validate_json(await websocket.receive_text())
    except WebSocketDisconnect:
        return
    except ValidationError:
        with contextlib.suppress(RuntimeError):
            await websocket.close(code=status.WS_1003_UNSUPPORTED_DATA)
        return

    live = LiveSession(websocket, transcriber, vad_factory(), start.language)
    worker = asyncio.create_task(live.run())
    await live.send({"type": "ready"})

    await _receive_audio(websocket, live)

    if live.overloaded:
        worker.cancel()
    else:
        await live.finish_input()
    with contextlib.suppress(asyncio.CancelledError):
        await worker

    await live.conclude(session, user_id)
    with contextlib.suppress(RuntimeError):
        await websocket.close()
