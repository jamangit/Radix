from collections import Counter
from functools import cache

import simplemma
import stopwordsiso
from wordfreq import zipf_frequency

from .models import AnalysisResult, Language, RareWord, WordCount
from .tokenizer import strip_elision, tokenize

DEFAULT_TOP_N = 10
DEFAULT_RARE_THRESHOLD = 3.5


@cache
def _stop_words(language: Language) -> frozenset[str]:
    return frozenset(stopwordsiso.stopwords(language))


def analyze_text(
    text: str,
    language: Language = "fr",
    *,
    top_n: int = DEFAULT_TOP_N,
    rare_threshold: float = DEFAULT_RARE_THRESHOLD,
) -> AnalysisResult:
    tokens = tokenize(text)
    stop_words = _stop_words(language)

    all_lemmas: list[str] = []
    content_lemmas: list[str] = []
    for token in tokens:
        word = strip_elision(token)
        lemma: str = simplemma.lemmatize(word, lang=language)
        all_lemmas.append(lemma)
        if word not in stop_words and lemma not in stop_words:
            content_lemmas.append(lemma)

    total = len(tokens)
    unique = len(set(all_lemmas))
    counts = Counter(content_lemmas)

    top_words = [WordCount(word=w, count=c) for w, c in counts.most_common(top_n)]

    # A zipf of 0 means the word is unknown to the dictionary (name, typo): not "rare", just noise.
    scored = sorted(((zipf_frequency(w, language), w) for w in counts), key=lambda p: (p[0], p[1]))
    rare_words = [RareWord(word=w, zipf=round(z, 2)) for z, w in scored if 0 < z < rare_threshold]

    return AnalysisResult(
        language=language,
        total_words=total,
        unique_words=unique,
        lexical_diversity=round(unique / total, 3) if total else 0.0,
        top_words=top_words,
        rare_words=rare_words[:top_n],
    )
