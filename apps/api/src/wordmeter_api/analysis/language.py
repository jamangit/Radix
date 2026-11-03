from functools import cache

from lingua import Language as LinguaLanguage
from lingua import LanguageDetector, LanguageDetectorBuilder

from .models import Language

_TO_CODE: dict[LinguaLanguage, Language] = {
    LinguaLanguage.FRENCH: "fr",
    LinguaLanguage.ENGLISH: "en",
}


@cache
def _detector() -> LanguageDetector:
    return LanguageDetectorBuilder.from_languages(*_TO_CODE).build()


def detect_language(text: str) -> tuple[Language, float]:
    """Return the most likely language and its confidence (0 to 1)."""
    best = _detector().compute_language_confidence_values(text)[0]
    if best.value == 0:
        return "fr", 0.0
    return _TO_CODE[best.language], best.value
