from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile, status

from wordmeter_api.analysis import AnalysisResult, Language, analyze_detailed
from wordmeter_api.config import settings
from wordmeter_api.dependencies import CurrentUser, SessionDep
from wordmeter_api.services.persistence import save_analysis
from wordmeter_api.speech.transcriber import (
    AudioTooLongError,
    InvalidAudioError,
    Transcriber,
    transcribe,
)

router = APIRouter(tags=["speech"])


class TranscribeResponse(AnalysisResult):
    transcript: str
    audio_seconds: float


def get_transcriber() -> Transcriber:
    return transcribe


TranscriberDep = Annotated[Transcriber, Depends(get_transcriber)]


def _resolve_language(requested: Language | None, detected: str) -> Language:
    if requested is not None:
        return requested
    if detected == "fr":
        return "fr"
    if detected == "en":
        return "en"
    raise HTTPException(
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        "Only French and English are supported for now.",
    )


@router.post("/transcribe", response_model=TranscribeResponse)
def transcribe_audio(
    audio: UploadFile,
    user: CurrentUser,
    session: SessionDep,
    transcriber: TranscriberDep,
    language: Annotated[Language | None, Form()] = None,
) -> TranscribeResponse:
    too_large = HTTPException(status.HTTP_413_CONTENT_TOO_LARGE, "Recording is too large")
    if audio.size is not None and audio.size > settings.max_audio_mb * 1024 * 1024:
        raise too_large
    try:
        transcription = transcriber(audio.file, language)
    except AudioTooLongError:
        raise too_large from None
    except InvalidAudioError:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, "Could not read this audio"
        ) from None

    if not transcription.text:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "No speech detected")

    chosen = _resolve_language(language, transcription.language)
    result, counts = analyze_detailed(transcription.text, chosen)
    save_analysis(session, user.id, result, counts)
    return TranscribeResponse(
        **result.model_dump(),
        transcript=transcription.text,
        audio_seconds=round(transcription.duration, 1),
    )
