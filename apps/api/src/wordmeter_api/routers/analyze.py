from fastapi import APIRouter
from pydantic import BaseModel, Field

from wordmeter_api.analysis import AnalysisResult, Language, analyze_detailed
from wordmeter_api.analysis.language import detect_language
from wordmeter_api.dependencies import CurrentUser, SessionDep
from wordmeter_api.services.persistence import save_analysis

router = APIRouter(tags=["analysis"])

MISMATCH_CONFIDENCE = 0.85


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
    save_analysis(session, user.id, result, counts)

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
