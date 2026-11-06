from pysilero_vad import SileroVoiceActivityDetector

from .segmenter import VoiceDetector


def create_voice_detector() -> VoiceDetector:
    """One detector per recording: Silero keeps internal state between frames."""
    detector = SileroVoiceActivityDetector()
    return detector  # callable: 512 samples of 16 kHz 16-bit PCM in, speech probability out
