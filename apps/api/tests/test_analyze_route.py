from fastapi.testclient import TestClient

ENGLISH_TEXT = "The weather is beautiful today and we are going to walk along the river."


def test_analyze_returns_statistics(auth_client: TestClient) -> None:
    payload = {"text": "Le chat mange. Le chat dort.", "language": "fr"}
    response = auth_client.post("/analyze", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["total_words"] == 6
    assert body["top_words"][0] == {"word": "chat", "count": 2}


def test_analyze_rejects_empty_text(auth_client: TestClient) -> None:
    assert auth_client.post("/analyze", json={"text": ""}).status_code == 422


def test_analyze_rejects_unsupported_language(auth_client: TestClient) -> None:
    response = auth_client.post("/analyze", json={"text": "hola", "language": "es"})

    assert response.status_code == 422


def test_auto_detects_english(auth_client: TestClient) -> None:
    body = auth_client.post("/analyze", json={"text": ENGLISH_TEXT}).json()

    assert body["language"] == "en"
    assert body["language_mismatch"] is False


def test_flags_language_mismatch_but_respects_choice(auth_client: TestClient) -> None:
    body = auth_client.post("/analyze", json={"text": ENGLISH_TEXT, "language": "fr"}).json()

    assert body["language"] == "fr"
    assert body["detected_language"] == "en"
    assert body["language_mismatch"] is True
