from tests.audio import energy_detector, loud, quiet
from wordmeter_api.speech.segmenter import SegmenterConfig, UtteranceSegmenter


def make_segmenter(**overrides: int) -> UtteranceSegmenter:
    return UtteranceSegmenter(energy_detector, SegmenterConfig(**overrides))


def test_a_phrase_is_returned_once_the_speaker_pauses() -> None:
    segmenter = make_segmenter()

    assert segmenter.feed(loud(640)) == []  # still talking: nothing yet
    phrases = segmenter.feed(quiet(640))

    assert len(phrases) == 1
    assert len(phrases[0]) >= len(loud(640))
    assert len(phrases[0]) < len(loud(640)) + len(quiet(640))  # most of the pause is dropped


def test_silence_alone_produces_nothing() -> None:
    segmenter = make_segmenter()

    assert segmenter.feed(quiet(4_992)) == []
    assert segmenter.flush() is None


def test_short_noise_bursts_are_ignored() -> None:
    segmenter = make_segmenter()

    phrases = segmenter.feed(loud(96) + quiet(1_024))  # a click or a knock

    assert phrases == []


def test_a_short_pause_does_not_split_a_phrase() -> None:
    segmenter = make_segmenter()

    phrases = segmenter.feed(loud(640) + quiet(224) + loud(640) + quiet(640))

    assert len(phrases) == 1


def test_a_long_pause_separates_two_phrases() -> None:
    segmenter = make_segmenter()

    phrases = segmenter.feed(loud(640) + quiet(800) + loud(640) + quiet(800))

    assert len(phrases) == 2


def test_the_start_of_the_phrase_is_kept() -> None:
    segmenter = make_segmenter()

    phrases = segmenter.feed(quiet(640) + loud(640) + quiet(640))

    assert phrases[0][:1024] == bytes(1024)  # pre-roll: the audio just before speech began


def test_flush_returns_the_phrase_in_progress() -> None:
    segmenter = make_segmenter()
    segmenter.feed(loud(640))

    phrase = segmenter.flush()

    assert phrase is not None
    assert len(phrase) >= len(loud(640))
    assert segmenter.flush() is None


def test_someone_who_never_pauses_is_cut_at_the_maximum_length() -> None:
    segmenter = make_segmenter(max_utterance_ms=2_048)

    phrases = segmenter.feed(loud(6_144))

    assert len(phrases) >= 2


def test_audio_can_arrive_in_arbitrary_chunk_sizes() -> None:
    segmenter = make_segmenter()
    audio = loud(640) + quiet(640)
    phrases: list[bytes] = []

    for start in range(0, len(audio), 1_000):
        phrases += segmenter.feed(audio[start : start + 1_000])

    assert len(phrases) == 1
    assert segmenter.in_speech is False
