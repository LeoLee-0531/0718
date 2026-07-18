from fastapi.testclient import TestClient


def test_home_and_manual_are_public(client: TestClient) -> None:
    home = client.get("/")
    manual = client.get("/manual")

    assert home.status_code == 200
    assert "Relay LLM" in home.text
    assert manual.status_code == 200
    assert "註冊與登入" in manual.text
    assert "http://127.0.0.1:8000/api/register" in manual.text
    assert "/v1/chat/completions" in manual.text
    assert "curl" in manual.text


def test_unknown_api_route_is_json(client: TestClient) -> None:
    response = client.get("/api/does-not-exist")
    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/json")
    assert response.json()["success"] is False
    assert response.json()["message"]["code"] == "not_found"
