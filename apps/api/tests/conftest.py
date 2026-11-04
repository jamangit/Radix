import os

os.environ.setdefault("JWT_SECRET", "test-secret-never-use-in-production-0123456789")

from collections.abc import Iterator  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from wordmeter_api.db import models  # noqa: E402, F401
from wordmeter_api.db.base import Base, get_session  # noqa: E402
from wordmeter_api.main import app  # noqa: E402


@pytest.fixture
def client() -> Iterator[TestClient]:
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    testing_session = sessionmaker(engine, expire_on_commit=False)

    def override_session() -> Iterator[Session]:
        with testing_session() as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    engine.dispose()


@pytest.fixture
def auth_client(client: TestClient) -> TestClient:
    credentials = {
        "name": "Ada Lovelace",
        "email": "ada@example.com",
        "password": "correct-horse-battery",
    }
    response = client.post("/auth/signup", json=credentials)
    assert response.status_code == 201
    return client
