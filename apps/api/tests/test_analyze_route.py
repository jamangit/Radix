from fastapi.testclient import TestClient

from wordmeter_api.main import app

client = TestClient(app)


def test_analyze_returns_statistics() -> None:
    payload = {"text": "Le chat mange. Le chat dort.", "language": "fr"}
    response = client.post("/analyze", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["total_words"] == 6
    assert body["top_words"][0] == {"word": "chat", "count": 2}


def test_analyze_rejects_empty_text() -> None:
    response = client.post("/analyze", json={"text": ""})

    assert response.status_code == 422


def test_analyze_rejects_unsupported_language() -> None:
    response = client.post("/analyze", json={"text": "hola", "language": "es"})

    assert response.status_code == 422
