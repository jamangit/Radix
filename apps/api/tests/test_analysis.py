import pytest

from wordmeter_api.analysis import analyze_text, analyzer


def test_counts_elided_words_as_one() -> None:
    result = analyze_text("L'homme mange. L'homme dort.", "fr")

    assert result.total_words == 4
    assert result.unique_words == 3
    assert result.top_words[0].word == "homme"
    assert result.top_words[0].count == 2


def test_excludes_stop_words_from_top_words() -> None:
    result = analyze_text("le chat et le chien", "fr")

    assert all(item.word not in {"le", "et"} for item in result.top_words)


def test_flags_rare_words(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_zipf = {"xylophone": 1.8, "maison": 5.1}
    monkeypatch.setattr(analyzer, "zipf_frequency", lambda word, lang: fake_zipf.get(word, 0.0))

    result = analyze_text("maison xylophone maison", "fr")

    assert [item.word for item in result.rare_words] == ["xylophone"]


def test_empty_text() -> None:
    result = analyze_text("   ")

    assert result.total_words == 0
    assert result.top_words == []
    assert result.lexical_diversity == 0.0
