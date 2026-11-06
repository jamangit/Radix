"""Tiny synthetic audio helpers: 16 kHz, 16-bit mono, so 1 ms = 32 bytes."""

import numpy as np

from wordmeter_api.speech.segmenter import FRAME_MS


def loud(ms: int) -> bytes:
    assert ms % FRAME_MS == 0
    return np.full(ms * 16, 8000, dtype=np.int16).tobytes()


def quiet(ms: int) -> bytes:
    assert ms % FRAME_MS == 0
    return bytes(ms * 32)


def energy_detector(frame: bytes) -> float:
    """Stand-in for the Silero model: anything clearly above silence counts as speech."""
    return 1.0 if np.abs(np.frombuffer(frame, dtype=np.int16)).max() > 1000 else 0.0
