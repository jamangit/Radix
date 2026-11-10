from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.testclient import WebSocketTestSession
from starlette.websockets import WebSocketDisconnect

from tests.audio import energy_detector, loud, quiet
from wordmeter_api.local import LOCAL_EMAIL, create_local_app
from wordmeter_api.routers.live import get_pcm_transcriber, get_vad_factory
from wordmeter_api.speech.transcriber import Transcription

BASE_URL = "http://127.0.0.1:8765"
PHRASE = "Le chat mange la souris."
# Starlette's test client always builds WebSocket URLs on "testserver": send the Host header
# a real browser would send, or the host check (rightly) refuses the connection.
WS_HEADERS = {"host": "127.0.0.1:8765"}


def fake_speech(app: FastAPI) -> None:
    """Replace Whisper and Silero so the tests need no model."""

    def fake_transcriber(pcm: bytes, language: str | None) -> Transcription:
        return Transcription(text=PHRASE, language="fr", duration=1.0)

    app.dependency_overrides[get_pcm_transcriber] = lambda: fake_transcriber
    app.dependency_overrides[get_vad_factory] = lambda: lambda: energy_detector


def read_final(ws: WebSocketTestSession) -> dict[str, Any]:
    for _ in range(20):
        message: dict[str, Any] = ws.receive_json()
        if message["type"] == "final":
            return message
    raise AssertionError("no final message received")


def speak_one_phrase(client: TestClient) -> None:
    ticket = client.post("/api/auth/ws-ticket").json()["ticket"]
    with client.websocket_connect(f"/api/ws/transcribe?ticket={ticket}", headers=WS_HEADERS) as ws:
        ws.send_json({"type": "start", "language": "fr"})
        assert ws.receive_json() == {"type": "ready"}
        ws.send_bytes(loud(640) + quiet(800))
        ws.send_json({"type": "stop"})
        read_final(ws)


@pytest.fixture
def local_app(tmp_path: Path) -> FastAPI:
    app = create_local_app(tmp_path / "data")
    fake_speech(app)
    return app


@pytest.fixture
def local_client(local_app: FastAPI) -> Iterator[TestClient]:
    with TestClient(local_app, base_url=BASE_URL) as client:
        yield client


def test_no_login_is_needed(local_client: TestClient) -> None:
    response = local_client.get("/api/auth/me")

    assert response.status_code == 200
    assert response.json()["email"] == LOCAL_EMAIL


def test_signup_and_login_do_not_exist_in_local_mode(local_client: TestClient) -> None:
    credentials = {"name": "Eve", "email": "eve@example.com", "password": "long-enough-password"}

    assert local_client.post("/api/auth/signup", json=credentials).status_code in (404, 405)
    assert local_client.post("/api/auth/login", json=credentials).status_code in (404, 405)


def test_speech_is_counted_and_stored_on_this_computer(
    local_client: TestClient, tmp_path: Path
) -> None:
    speak_one_phrase(local_client)

    stats = local_client.get("/api/stats", params={"period": "day"}).json()

    assert stats["total_words"] == 5
    assert (tmp_path / "data" / "wordmeter.db").exists()


def test_data_survives_a_restart(tmp_path: Path) -> None:
    first = create_local_app(tmp_path / "data")
    fake_speech(first)
    with TestClient(first, base_url=BASE_URL) as client:
        speak_one_phrase(client)

    second = create_local_app(tmp_path / "data")
    with TestClient(second, base_url=BASE_URL) as client:
        stats = client.get("/api/stats", params={"period": "day"}).json()

    assert stats["total_words"] == 5


def test_requests_for_another_host_name_are_refused(local_client: TestClient) -> None:
    response = local_client.get("/api/health", headers={"host": "evil.example"})

    assert response.status_code == 400


def test_requests_coming_from_another_site_are_refused(local_client: TestClient) -> None:
    hostile = local_client.get("/api/health", headers={"origin": "https://evil.example"})
    friendly = local_client.get("/api/health", headers={"origin": BASE_URL})

    assert hostile.status_code == 403
    assert friendly.status_code == 200


def test_a_hostile_site_cannot_open_the_websocket(local_client: TestClient) -> None:
    ticket = local_client.post("/api/auth/ws-ticket").json()["ticket"]

    with (
        pytest.raises(WebSocketDisconnect) as refused,
        local_client.websocket_connect(
            f"/api/ws/transcribe?ticket={ticket}",
            headers={**WS_HEADERS, "origin": "https://evil.example"},
        ),
    ):
        pass

    assert refused.value.code == 1008  # refused by the origin guard, not by the host check


def test_the_web_app_is_served_from_the_same_address(tmp_path: Path) -> None:
    web = tmp_path / "web"
    (web / "dashboard").mkdir(parents=True)
    (web / "index.html").write_text("<h1>Radix</h1>")
    (web / "dashboard" / "index.html").write_text("<h1>Dashboard</h1>")
    app = create_local_app(tmp_path / "data", web_dir=web)

    with TestClient(app, base_url=BASE_URL) as client:
        assert "Radix" in client.get("/").text
        assert "Dashboard" in client.get("/dashboard/").text
        assert client.get("/api/health").json()["mode"] == "local"
