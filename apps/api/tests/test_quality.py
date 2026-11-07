import numpy as np

from tests.audio import quiet
from wordmeter_api.speech.quality import AudioQuality, measure_quality

RATE = 16_000
MIN_LEVEL = -45.0
MIN_SNR = 12.0


def voice(ms: int, amplitude: float) -> bytes:
    """A 200 Hz tone standing in for a voice."""
    t = np.arange(ms * RATE // 1000) / RATE
    return (amplitude * np.sin(2 * np.pi * 200 * t)).astype(np.int16).tobytes()


def noise(ms: int, deviation: float) -> bytes:
    rng = np.random.default_rng(0)
    return rng.normal(0, deviation, ms * RATE // 1000).astype(np.int16).tobytes()


def judge(pcm: bytes) -> AudioQuality:
    return measure_quality(pcm, min_level_db=MIN_LEVEL, min_snr_db=MIN_SNR)


def test_a_clear_voice_close_to_the_microphone_is_fine() -> None:
    quality = judge(quiet(256) + voice(640, 3_000) + quiet(128))

    assert quality.verdict == "ok"
    assert -30 < quality.level_db < -20


def test_a_faint_voice_means_the_speaker_is_too_far() -> None:
    quality = judge(quiet(256) + voice(640, 100) + quiet(128))

    assert quality.verdict == "too_quiet"
    assert quality.level_db < MIN_LEVEL


def test_a_voice_buried_in_background_noise_is_flagged() -> None:
    pcm = noise(256, 800) + voice(640, 3_000) + noise(128, 800)

    assert judge(pcm).verdict == "noisy"


def test_a_distorted_voice_is_too_loud() -> None:
    quality = judge(quiet(256) + voice(640, 32_767) + quiet(128))

    assert quality.verdict == "too_loud"


def test_the_louder_the_voice_the_higher_the_level() -> None:
    soft = judge(quiet(256) + voice(640, 500) + quiet(128))
    firm = judge(quiet(256) + voice(640, 5_000) + quiet(128))

    assert firm.level_db > soft.level_db
    assert firm.snr_db > soft.snr_db


def test_a_clip_shorter_than_one_frame_is_not_judged() -> None:
    assert judge(bytes(100)).verdict == "ok"
