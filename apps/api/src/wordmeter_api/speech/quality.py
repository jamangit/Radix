from dataclasses import dataclass
from typing import Literal

import numpy as np

from .segmenter import FRAME_SAMPLES

Verdict = Literal["ok", "too_quiet", "noisy", "too_loud"]

FULL_SCALE = 32768.0
CLIPPING_SAMPLE = 32000  # close to the maximum a 16-bit sample can hold
CLIPPING_FRACTION = 0.005  # more than 0.5 % of samples at the limit means the sound is distorted


@dataclass(frozen=True)
class AudioQuality:
    level_db: float  # loudness of the voice, in dB below full scale (0 is the maximum)
    snr_db: float  # how far the voice stands above the background, in dB
    verdict: Verdict


def measure_quality(pcm: bytes, *, min_level_db: float, min_snr_db: float) -> AudioQuality:
    """Judge one phrase of 16 kHz 16-bit mono PCM: is the speaker close enough, is it clean?

    A phrase starts and ends with a little silence, so the quietest frames approximate the
    background noise and the loudest ones the voice.
    """
    samples = np.frombuffer(pcm, dtype=np.int16)
    usable = len(samples) // FRAME_SAMPLES * FRAME_SAMPLES
    if usable == 0:
        return AudioQuality(level_db=-96.0, snr_db=0.0, verdict="ok")

    frames = samples[:usable].astype(np.float64).reshape(-1, FRAME_SAMPLES)
    rms = np.sqrt((frames**2).mean(axis=1))
    levels = 20 * np.log10(np.maximum(rms, 1.0) / FULL_SCALE)
    voice_db = float(np.percentile(levels, 90))
    noise_db = float(np.percentile(levels, 10))
    snr_db = voice_db - noise_db
    clipped = float((np.abs(samples.astype(np.int32)) >= CLIPPING_SAMPLE).mean())

    verdict: Verdict = "ok"
    if clipped > CLIPPING_FRACTION:
        verdict = "too_loud"
    elif voice_db < min_level_db:
        verdict = "too_quiet"
    elif snr_db < min_snr_db:
        verdict = "noisy"
    return AudioQuality(level_db=round(voice_db, 1), snr_db=round(snr_db, 1), verdict=verdict)
