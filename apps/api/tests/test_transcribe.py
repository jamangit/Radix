from typing import BinaryIO

import pytest
from fastapi.testclient import TestClient

from wordmeter_api.config import settings
from wordmeter_api.main import app
from wordmeter_api.routers.transcribe import get_transcriber
from wordmeter_api.speech.transcriber import AudioTooLongError, Transcription

AUDIO = {"audio": ("clip.webm", b"not-real-audio", "audio/webm")}


def use_fake_transcriber(
    text: str = "Le chat mange la souris. Le chat dort.", spoken_language: str = "fr"
) -> None:
    def fake(audio: BinaryIO, language: str | None) -> Transcription:
        return Transcription(text=text, language=spoken_language, duration=5.0)

    app.dependency_overrides[get_transcriber] = lambda: fake


def test_transcribe_requires_authentication(client: TestClient) -> None:
    assert client.post("/transcribe", files=AUDIO).status_code == 401


def test_transcribe_returns_transcript_and_feeds_the_recap(auth_client: TestClient) -> None:
    use_fake_transcriber()

    response = auth_client.post("/transcribe", files=AUDIO)

    assert response.status_code == 200
    body = response.json()
    assert body["transcript"] == "Le chat mange la souris. Le chat dort."
    assert body["total_words"] == 8
    assert body["top_words"][0] == {"word": "chat", "count": 2}
    stats = auth_client.get("/stats", params={"period": "day"}).json()
    assert stats["total_words"] == 8


def test_transcribe_rejects_silence(auth_client: TestClient) -> None:
    use_fake_transcriber(text="")

    assert auth_client.post("/transcribe", files=AUDIO).status_code == 422


def test_transcribe_rejects_unsupported_languages(auth_client: TestClient) -> None:
    use_fake_transcriber(spoken_language="de")

    response = auth_client.post("/transcribe", files=AUDIO)

    assert response.status_code == 422
    assert "French and English" in response.json()["detail"]


def test_transcribe_rejects_recordings_that_are_too_long(auth_client: TestClient) -> None:
    def too_long(audio: BinaryIO, language: str | None) -> Transcription:
        raise AudioTooLongError

    app.dependency_overrides[get_transcriber] = lambda: too_long

    assert auth_client.post("/transcribe", files=AUDIO).status_code == 413


def test_transcribe_rejects_oversized_uploads(
    auth_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    use_fake_transcriber()
    monkeypatch.setattr(settings, "max_audio_mb", 0)

    assert auth_client.post("/transcribe", files=AUDIO).status_code == 413
