from fastapi import APIRouter
from pydantic import BaseModel, Field

from wordmeter_api.analysis import AnalysisResult, Language, analyze_text
from wordmeter_api.analysis.language import detect_language

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
def analyze(payload: AnalyzeRequest) -> AnalyzeResponse:
    detected, confidence = detect_language(payload.text)
    language = payload.language or detected
    result = analyze_text(payload.text, language)

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
