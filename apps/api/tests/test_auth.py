from fastapi.testclient import TestClient

ADA = {"name": "Ada Lovelace", "email": "ada@example.com", "password": "correct-horse-battery"}


def test_signup_logs_the_user_in(client: TestClient) -> None:
    response = client.post("/auth/signup", json=ADA)

    assert response.status_code == 201
    assert response.json()["email"] == "ada@example.com"
    assert "password" not in response.text

    me = client.get("/auth/me")
    assert me.status_code == 200
    assert me.json()["name"] == "Ada Lovelace"


def test_signup_rejects_duplicate_email_ignoring_case(client: TestClient) -> None:
    client.post("/auth/signup", json=ADA)

    response = client.post("/auth/signup", json={**ADA, "email": "ADA@example.com"})

    assert response.status_code == 409


def test_signup_rejects_short_password(client: TestClient) -> None:
    response = client.post("/auth/signup", json={**ADA, "password": "short"})

    assert response.status_code == 422


def test_login_with_correct_credentials(client: TestClient) -> None:
    client.post("/auth/signup", json=ADA)
    client.post("/auth/logout")

    response = client.post(
        "/auth/login", json={"email": "ada@example.com", "password": ADA["password"]}
    )

    assert response.status_code == 200
    assert client.get("/auth/me").status_code == 200


def test_login_rejects_wrong_password_and_unknown_email_the_same_way(
    client: TestClient,
) -> None:
    client.post("/auth/signup", json=ADA)

    wrong_password = client.post(
        "/auth/login", json={"email": "ada@example.com", "password": "wrong-password"}
    )
    unknown_email = client.post(
        "/auth/login", json={"email": "nobody@example.com", "password": "wrong-password"}
    )

    assert wrong_password.status_code == unknown_email.status_code == 401
    assert wrong_password.json() == unknown_email.json()


def test_me_requires_authentication(client: TestClient) -> None:
    assert client.get("/auth/me").status_code == 401


def test_logout_ends_the_session(client: TestClient) -> None:
    client.post("/auth/signup", json=ADA)

    assert client.post("/auth/logout").status_code == 204
    assert client.get("/auth/me").status_code == 401
