import re

_WORD_RE = re.compile(r"[^\W\d_]+(?:['-][^\W\d_]+)*")
_ELISIONS = frozenset({"l", "d", "j", "m", "n", "s", "t", "c", "qu", "jusqu", "lorsqu", "puisqu"})


def tokenize(text: str) -> list[str]:
    normalized = text.lower().replace("’", "'")
    return _WORD_RE.findall(normalized)


def strip_elision(token: str) -> str:
    """Turn "l'homme" into "homme" so vocabulary stats ignore the elided article."""
    prefix, separator, rest = token.partition("'")
    if separator and prefix in _ELISIONS:
        return rest
    return token
