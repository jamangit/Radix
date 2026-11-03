from typing import Literal

from pydantic import BaseModel

Language = Literal["fr", "en"]


class WordCount(BaseModel):
    word: str
    count: int


class RareWord(BaseModel):
    word: str
    zipf: float


class AnalysisResult(BaseModel):
    language: Language
    total_words: int
    unique_words: int
    lexical_diversity: float
    top_words: list[WordCount]
    rare_words: list[RareWord]
