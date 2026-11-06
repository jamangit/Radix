import math
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass

SAMPLE_RATE = 16_000
BYTES_PER_SECOND = SAMPLE_RATE * 2  # 16-bit mono
FRAME_SAMPLES = 512  # what the Silero voice detector expects
FRAME_BYTES = FRAME_SAMPLES * 2
FRAME_MS = FRAME_SAMPLES * 1000 // SAMPLE_RATE  # 32 ms

VoiceDetector = Callable[[bytes], float]


def _frames(milliseconds: int) -> int:
    return max(1, math.ceil(milliseconds / FRAME_MS))


@dataclass(frozen=True)
class SegmenterConfig:
    start_threshold: float = 0.5
    end_threshold: float = 0.35
    min_silence_ms: int = 500  # pause that ends a phrase
    min_speech_ms: int = 250  # shorter bursts (clicks, bumps, coughs) are dropped
    pre_roll_ms: int = 256  # audio kept before speech starts, so the first syllable survives
    trailing_ms: int = 128  # silence kept after speech
    max_utterance_ms: int = 25_000  # hard cut for people who never pause


class UtteranceSegmenter:
    """Cuts a continuous 16 kHz PCM stream into spoken phrases, dropping silence and noise."""

    def __init__(self, detector: VoiceDetector, config: SegmenterConfig | None = None) -> None:
        cfg = config or SegmenterConfig()
        self._detector = detector
        self._start = cfg.start_threshold
        self._end = cfg.end_threshold
        self._silence_limit = _frames(cfg.min_silence_ms)
        self._min_speech = _frames(cfg.min_speech_ms)
        self._trailing = _frames(cfg.trailing_ms)
        self._max_frames = _frames(cfg.max_utterance_ms)
        self._pre_roll: deque[bytes] = deque(maxlen=_frames(cfg.pre_roll_ms))
        self._pending = bytearray()
        self._frames: list[bytes] = []
        self._in_speech = False
        self._speech_frames = 0
        self._silence_frames = 0

    @property
    def in_speech(self) -> bool:
        return self._in_speech

    def feed(self, pcm: bytes) -> list[bytes]:
        """Add audio and return the phrases completed by it (usually none or one)."""
        self._pending.extend(pcm)
        phrases: list[bytes] = []
        while len(self._pending) >= FRAME_BYTES:
            frame = bytes(self._pending[:FRAME_BYTES])
            del self._pending[:FRAME_BYTES]
            phrase = self._push(frame)
            if phrase is not None:
                phrases.append(phrase)
        return phrases

    def flush(self) -> bytes | None:
        """End of the recording: return the phrase in progress, if any."""
        phrase = self._finish()
        self._pending.clear()
        return phrase

    def _push(self, frame: bytes) -> bytes | None:
        probability = self._detector(frame)

        if not self._in_speech:
            self._pre_roll.append(frame)
            if probability >= self._start:
                self._in_speech = True
                self._frames = list(self._pre_roll)
                self._pre_roll.clear()
                self._speech_frames = 1
                self._silence_frames = 0
            return None

        self._frames.append(frame)
        if probability >= self._end:
            self._silence_frames = 0
            if probability >= self._start:
                self._speech_frames += 1
        else:
            self._silence_frames += 1

        if self._silence_frames >= self._silence_limit or len(self._frames) >= self._max_frames:
            return self._finish()
        return None

    def _finish(self) -> bytes | None:
        if not self._in_speech:
            return None
        frames = self._frames
        enough_speech = self._speech_frames >= self._min_speech
        extra_silence = self._silence_frames - self._trailing
        if extra_silence > 0:
            frames = frames[:-extra_silence]
        self._in_speech = False
        self._frames = []
        self._speech_frames = 0
        self._silence_frames = 0
        self._pre_roll.clear()
        return b"".join(frames) if enough_speech else None
