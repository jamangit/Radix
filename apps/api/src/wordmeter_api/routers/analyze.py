from fastapi import APIRouter
from pydantic import BaseModel, Field

from wordmeter_api.analysis import AnalysisResult, Language, analyze_text

router = APIRouter(tags=["analysis"])


class AnalyzeRequest(BaseModel):
    text: str = Field(min_length=1, max_length=50_000)
    language: Language = "fr"


@router.post("/analyze", response_model=AnalysisResult)
def analyze(payload: AnalyzeRequest) -> AnalysisResult:
    return analyze_text(payload.text, payload.language)
