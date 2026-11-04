from fastapi import APIRouter
from pydantic import BaseModel, Field

from wordmeter_api.analysis import AnalysisResult, Language, analyze_detailed
from wordmeter_api.analysis.language import detect_language
from wordmeter_api.db.models import Analysis, AnalysisWord
from wordmeter_api.dependencies import CurrentUser, SessionDep

router = APIRouter(tags=["analysis"])

MISMATCH_CONFIDENCE = 0.85
MAX_WORD_LENGTH = 100


class AnalyzeRequest(BaseModel):
    text: str = Field(min_length=1, max_length=50_000)
    language: Language | None = None  # None means auto-detect


class AnalyzeResponse(AnalysisResult):
    detected_language: Language
    detection_confidence: float
    language_mismatch: bool


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze(payload: AnalyzeRequest, user: CurrentUser, session: SessionDep) -> AnalyzeResponse:
    detected, confidence = detect_language(payload.text)
    language = payload.language or detected
    result, counts = analyze_detailed(payload.text, language)

    if result.total_words > 0:
        session.add(
            Analysis(
                user_id=user.id,
                language=language,
                total_words=result.total_words,
                unique_words=result.unique_words,
                words=[
                    AnalysisWord(word=word, count=count)
                    for word, count in counts.items()
                    if len(word) <= MAX_WORD_LENGTH
                ],
            )
        )
        session.commit()

    mismatch = (
        payload.language is not None
        and payload.language != detected
        and confidence >= MISMATCH_CONFIDENCE
    )
    return AnalyzeResponse(
        **result.model_dump(),
        detected_language=detected,
        detection_confidence=round(confidence, 2),
        language_mismatch=mismatch,
    )
