import threading
from dataclasses import dataclass
from functools import cache
from typing import BinaryIO, Protocol

from faster_whisper import WhisperModel

from wordmeter_api.config import settings


class AudioTooLongError(Exception):
    """The recording is longer than the configured limit."""


class InvalidAudioError(Exception):
    """The uploaded file could not be decoded as audio."""


@dataclass(frozen=True)
class Transcription:
    text: str
    language: str
    duration: float


class Transcriber(Protocol):
    def __call__(self, audio: BinaryIO, language: str | None) -> Transcription: ...


# Whisper is CPU and memory hungry: only one transcription runs at a time.
_lock = threading.Lock()


@cache
def _model() -> WhisperModel:
    return WhisperModel(
        settings.whisper_model, device="cpu", compute_type=settings.whisper_compute_type
    )


def transcribe(audio: BinaryIO, language: str | None = None) -> Transcription:
    with _lock:
        model = _model()
        try:
            segments, info = model.transcribe(audio, language=language, vad_filter=True)
        except Exception as error:
            raise InvalidAudioError from error
        if info.duration > settings.max_audio_seconds:
            raise AudioTooLongError
        text = " ".join(segment.text.strip() for segment in segments).strip()
    return Transcription(text=text, language=info.language, duration=info.duration)
