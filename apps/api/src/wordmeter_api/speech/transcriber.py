import re
import threading
from collections.abc import Iterable
from dataclasses import dataclass
from functools import cache
from typing import TYPE_CHECKING, BinaryIO, Protocol

import numpy as np

from wordmeter_api.config import settings

from .segmenter import SAMPLE_RATE

if TYPE_CHECKING:
    from faster_whisper import WhisperModel
    from faster_whisper.transcribe import Segment


class AudioTooLongError(Exception):
    """The recording is longer than the configured limit."""


class InvalidAudioError(Exception):
    """The uploaded file could not be decoded as audio."""


@dataclass(frozen=True)
class Transcription:
    text: str
    language: str
    duration: float
    language_probability: float = 1.0


class Transcriber(Protocol):
    def __call__(self, audio: BinaryIO, language: str | None) -> Transcription: ...


# Whisper is CPU and memory hungry: only one transcription runs at a time.
_lock = threading.Lock()

# Phrases Whisper tends to invent on silence or noise (subtitle credits, outros).
_HALLUCINATIONS = frozenset(
    {
        "sous titrage st 501",
        "sous titres realises par la communaute d amara org",
        "sous titrage societe radio canada",
        "merci d avoir regarde cette video",
        "merci d avoir regarde la video",
        "thank you for watching",
        "thanks for watching",
        "please subscribe",
    }
)


@cache
def _model() -> "WhisperModel":
    from faster_whisper import WhisperModel

    return WhisperModel(
        settings.whisper_model, device="cpu", compute_type=settings.whisper_compute_type
    )


def warm_up() -> None:
    """Load the model and run it once, so the first real phrase is not slow."""
    transcribe_pcm(bytes(SAMPLE_RATE * 2), "fr")


def _normalize(text: str) -> str:
    return re.sub(r"[^\w]+", " ", text.lower().replace("'", " ")).strip()


def _keep(segment: "Segment") -> bool:
    """Drop segments that look like noise decoded as speech."""
    if segment.no_speech_prob > 0.6 and segment.avg_logprob < -1.0:
        return False
    if segment.compression_ratio > 2.4:  # repetitive loops are a classic hallucination
        return False
    return _normalize(segment.text) not in _HALLUCINATIONS


def _join(segments: "Iterable[Segment]") -> str:
    return " ".join(s.text.strip() for s in segments if _keep(s)).strip()


def transcribe(audio: BinaryIO, language: str | None = None) -> Transcription:
    """Transcribe an uploaded audio file (any format the browser records)."""
    with _lock:
        model = _model()
        try:
            segments, info = model.transcribe(audio, language=language, vad_filter=True)
        except Exception as error:
            raise InvalidAudioError from error
        if info.duration > settings.max_audio_seconds:
            raise AudioTooLongError
        text = _join(segments)
    return Transcription(
        text=text,
        language=info.language,
        duration=info.duration,
        language_probability=info.language_probability,
    )


def transcribe_pcm(pcm: bytes, language: str | None = None) -> Transcription:
    """Transcribe one phrase of 16 kHz 16-bit mono PCM, tuned for speed."""
    samples = np.frombuffer(pcm, dtype=np.int16).astype(np.float32) / 32768.0
    with _lock:
        segments, info = _model().transcribe(
            samples,
            language=language,
            beam_size=1,  # greedy decoding: noticeably faster, small accuracy cost
            temperature=0.0,  # no slow re-decoding at higher temperatures
            condition_on_previous_text=False,
            without_timestamps=True,
            vad_filter=False,  # the audio was already cut on speech
        )
        text = _join(segments)
    return Transcription(
        text=text,
        language=info.language,
        duration=len(samples) / SAMPLE_RATE,
        language_probability=info.language_probability,
    )
