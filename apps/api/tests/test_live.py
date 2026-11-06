from typing import Any

import pytest
from fastapi.testclient import TestClient
from starlette.testclient import WebSocketTestSession
from starlette.websockets import WebSocketDisconnect

from tests.audio import energy_detector, loud, quiet
from wordmeter_api.config import settings
from wordmeter_api.main import app
from wordmeter_api.routers.live import get_pcm_transcriber, get_vad_factory
from wordmeter_api.speech.transcriber import Transcription

PHRASE = "Le chat mange la souris."


def use_fakes(
    text: str = PHRASE, language: str = "fr", probability: float = 1.0
) -> list[str | None]:
    """Replace Whisper and Silero; returns the languages Whisper was asked to use."""
    asked: list[str | None] = []

    def fake_transcriber(pcm: bytes, requested: str | None) -> Transcription:
        asked.append(requested)
        return Transcription(
            text=text, language=language, duration=1.0, language_probability=probability
        )

    app.dependency_overrides[get_pcm_transcriber] = lambda: fake_transcriber
    app.dependency_overrides[get_vad_factory] = lambda: lambda: energy_detector
    return asked


def open_session(client: TestClient) -> Any:
    ticket = client.post("/auth/ws-ticket").json()["ticket"]
    return client.websocket_connect(f"/ws/transcribe?ticket={ticket}")


def start(ws: WebSocketTestSession, language: str | None = "fr") -> None:
    ws.send_json({"type": "start", "language": language})
    assert ws.receive_json() == {"type": "ready"}


def read_until(ws: WebSocketTestSession, kind: str) -> dict[str, Any]:
    for _ in range(20):
        message: dict[str, Any] = ws.receive_json()
        if message["type"] == kind:
            return message
    raise AssertionError(f"no {kind} message received")


def test_a_phrase_is_transcribed_while_the_recording_continues(auth_client: TestClient) -> None:
    use_fakes()

    with open_session(auth_client) as ws:
        start(ws)
        ws.send_bytes(loud(640))
        assert read_until(ws, "speech")["active"] is True
        ws.send_bytes(quiet(640))

        segment = read_until(ws, "segment")  # arrives before the user pressed stop

        assert segment["text"] == PHRASE
        assert segment["words"] == 5
        assert segment["total_words"] == 5


def test_the_running_count_adds_up_and_the_session_is_saved(auth_client: TestClient) -> None:
    use_fakes()

    with open_session(auth_client) as ws:
        start(ws)
        for _ in range(2):
            ws.send_bytes(loud(640) + quiet(800))
            last = read_until(ws, "segment")
        assert last["total_words"] == 10
        ws.send_json({"type": "stop"})
        final = read_until(ws, "final")

    assert final["total_words"] == 10
    assert final["top_words"][0] == {"word": "chat", "count": 2}
    stats = auth_client.get("/stats", params={"period": "day"})
    assert stats.json()["total_words"] == 10


def test_stopping_mid_phrase_still_transcribes_it(auth_client: TestClient) -> None:
    use_fakes()

    with open_session(auth_client) as ws:
        start(ws)
        ws.send_bytes(loud(640))
        ws.send_json({"type": "stop"})
        final = read_until(ws, "final")

    assert final["transcript"] == PHRASE


def test_noise_only_is_reported_as_no_speech(auth_client: TestClient) -> None:
    use_fakes()

    with open_session(auth_client) as ws:
        start(ws)
        ws.send_bytes(loud(96) + quiet(1_024))  # a knock on the desk
        ws.send_json({"type": "stop"})
        error = read_until(ws, "error")

    assert error["code"] == "no_speech"


def test_auto_mode_locks_the_language_once_whisper_is_sure(auth_client: TestClient) -> None:
    asked = use_fakes(language="en", probability=0.95)

    with open_session(auth_client) as ws:
        start(ws, language=None)
        for _ in range(2):
            ws.send_bytes(loud(640) + quiet(800))
            read_until(ws, "segment")

    assert asked == [None, "en"]


def test_auto_mode_rejects_unsupported_languages(auth_client: TestClient) -> None:
    use_fakes(language="de", probability=0.95)

    with open_session(auth_client) as ws:
        start(ws, language=None)
        ws.send_bytes(loud(640) + quiet(800))
        error = read_until(ws, "error")

    assert error["code"] == "unsupported_language"


def test_a_ticket_is_required(client: TestClient) -> None:
    use_fakes()

    with pytest.raises(WebSocketDisconnect), client.websocket_connect("/ws/transcribe?ticket=nope"):
        pass


def test_a_session_cookie_is_not_accepted_as_a_ticket(auth_client: TestClient) -> None:
    use_fakes()
    cookie = auth_client.cookies["access_token"]

    with (
        pytest.raises(WebSocketDisconnect),
        auth_client.websocket_connect(f"/ws/transcribe?ticket={cookie}"),
    ):
        pass


def test_a_ticket_is_not_accepted_as_a_session(auth_client: TestClient) -> None:
    ticket = auth_client.post("/auth/ws-ticket").json()["ticket"]
    auth_client.cookies.clear()
    auth_client.cookies.set("access_token", ticket)

    assert auth_client.get("/auth/me").status_code == 401


def test_the_ticket_endpoint_requires_a_login(client: TestClient) -> None:
    assert client.post("/auth/ws-ticket").status_code == 401


def test_recordings_are_limited_in_length(
    auth_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    use_fakes()
    monkeypatch.setattr(settings, "max_stream_seconds", 1)

    with open_session(auth_client) as ws:
        start(ws)
        ws.send_bytes(loud(2_048))
        error = read_until(ws, "error")

    assert error["code"] == "too_long"


def test_a_malformed_first_message_is_rejected(auth_client: TestClient) -> None:
    use_fakes()

    with open_session(auth_client) as ws:
        ws.send_text("hello")
        with pytest.raises(WebSocketDisconnect):
            ws.receive_json()
