from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client(tmp_path) -> Iterator[TestClient]:
    application = create_app(str(tmp_path / "test.db"), production=False)
    with TestClient(application) as test_client:
        yield test_client


@pytest.fixture
def registered_client(client: TestClient) -> TestClient:
    response = client.post(
        "/api/register",
        json={"username": "alice", "password": "correct-horse-battery-staple"},
    )
    assert response.status_code == 201
    response = client.post(
        "/api/login",
        json={"username": "alice", "password": "correct-horse-battery-staple"},
    )
    assert response.status_code == 200
    return client


@pytest.fixture
def api_key(registered_client: TestClient) -> str:
    response = registered_client.post("/api/keys")
    assert response.status_code == 200
    return response.json()["message"]["api_key"]
