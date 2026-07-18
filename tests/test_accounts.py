from fastapi.testclient import TestClient

from app.security import SESSION_COOKIE


def test_register_hashes_password_and_rejects_duplicate(client: TestClient) -> None:
    credentials = {"username": "Alice_01", "password": "a-secure-password"}
    response = client.post("/api/register", json=credentials)

    assert response.status_code == 201
    assert response.json() == {"success": True, "message": {"detail": "Account created."}}

    row = client.app.state.db.fetch_one(
        "SELECT username, password_hash FROM users WHERE username = ?", ("Alice_01",)
    )
    assert row["username"] == "Alice_01"
    assert row["password_hash"] != credentials["password"]
    assert row["password_hash"].startswith("$argon2")

    duplicate = client.post(
        "/api/register", json={"username": "alice_01", "password": "another-password"}
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["success"] is False
    assert duplicate.json()["message"]["code"] == "username_exists"


def test_registration_validation_uses_json_error_shape(client: TestClient) -> None:
    response = client.post("/api/register", json={"username": "x", "password": "short"})

    assert response.status_code == 400
    assert response.headers["content-type"].startswith("application/json")
    assert response.json()["success"] is False
    assert response.json()["message"]["code"] == "invalid_request"


def test_login_sets_secure_session_properties(client: TestClient) -> None:
    credentials = {"username": "alice", "password": "correct-horse-battery-staple"}
    client.post("/api/register", json=credentials)

    invalid = client.post("/api/login", json={**credentials, "password": "wrong-password"})
    assert invalid.status_code == 401
    assert invalid.json()["message"]["code"] == "invalid_credentials"

    response = client.post("/api/login", json=credentials)
    cookie = response.headers["set-cookie"]
    assert response.status_code == 200
    assert f"{SESSION_COOKIE}=" in cookie
    assert "HttpOnly" in cookie
    assert "SameSite=lax" in cookie
    assert "Path=/" in cookie

    session_value = client.cookies.get(SESSION_COOKIE)
    row = client.app.state.db.fetch_one("SELECT token_hash FROM sessions")
    assert row["token_hash"] != session_value


def test_api_key_requires_login_and_is_never_stored_plaintext(
    client: TestClient, registered_client: TestClient
) -> None:
    anonymous = TestClient(client.app)
    response = anonymous.post("/api/keys")
    assert response.status_code == 401
    assert response.json() == {
        "success": False,
        "message": {"code": "unauthorized", "detail": "Please sign in to continue."},
    }

    created = registered_client.post("/api/keys")
    api_key = created.json()["message"]["api_key"]
    assert created.status_code == 200
    assert api_key.startswith("llm_live_")

    row = registered_client.app.state.db.fetch_one("SELECT key_hash, key_prefix FROM api_keys")
    assert row["key_hash"] != api_key
    assert api_key not in row["key_hash"]

    account = registered_client.get("/api/me").json()["message"]
    assert account["username"] == "alice"
    assert account["keys"][0]["name"] == "Untitled key"
    assert account["keys"][0]["display"].endswith("...")
    assert api_key not in account["keys"][0]["display"]


def test_api_key_names_can_be_set_and_edited(registered_client: TestClient) -> None:
    created = registered_client.post("/api/keys", json={"name": "  Production  "})
    assert created.status_code == 200
    key = registered_client.get("/api/me").json()["message"]["keys"][0]
    assert key["name"] == "Production"

    invalid = registered_client.patch(f"/api/keys/{key['id']}", json={"name": "   "})
    assert invalid.status_code == 400
    assert invalid.json()["message"]["code"] == "invalid_request"

    registered_client.post(
        "/api/register",
        json={"username": "bob", "password": "another-secure-password"},
    )
    registered_client.post(
        "/api/login",
        json={"username": "bob", "password": "another-secure-password"},
    )
    other_user = registered_client.patch(f"/api/keys/{key['id']}", json={"name": "Stolen"})
    assert other_user.status_code == 404
    assert other_user.json()["message"]["code"] == "api_key_not_found"

    registered_client.post(
        "/api/login",
        json={"username": "alice", "password": "correct-horse-battery-staple"},
    )
    renamed = registered_client.patch(f"/api/keys/{key['id']}", json={"name": "Staging"})
    assert renamed.status_code == 200
    assert renamed.json() == {"success": True, "message": {"name": "Staging"}}
    account = registered_client.get("/api/me").json()["message"]
    assert account["keys"][0]["name"] == "Staging"


def test_api_key_removal_enforces_ownership_and_revokes_access(
    registered_client: TestClient,
) -> None:
    first_key = registered_client.post("/api/keys").json()["message"]["api_key"]
    second_key = registered_client.post("/api/keys").json()["message"]["api_key"]
    account = registered_client.get("/api/me").json()["message"]
    first_key_id = next(
        key["id"] for key in account["keys"] if first_key.startswith(key["display"][:-3])
    )
    second_key_id = next(
        key["id"] for key in account["keys"] if second_key.startswith(key["display"][:-3])
    )

    anonymous = TestClient(registered_client.app)
    unauthorized = anonymous.delete(f"/api/keys/{first_key_id}")
    assert unauthorized.status_code == 401
    assert unauthorized.json()["message"]["code"] == "unauthorized"

    registered_client.post(
        "/api/register",
        json={"username": "bob", "password": "another-secure-password"},
    )
    registered_client.post(
        "/api/login",
        json={"username": "bob", "password": "another-secure-password"},
    )
    other_user = registered_client.delete(f"/api/keys/{first_key_id}")
    assert other_user.status_code == 404
    assert other_user.json()["message"]["code"] == "api_key_not_found"

    registered_client.post(
        "/api/login",
        json={"username": "alice", "password": "correct-horse-battery-staple"},
    )
    removed = registered_client.delete(f"/api/keys/{first_key_id}")
    assert removed.status_code == 200
    assert removed.json() == {"success": True, "message": {"detail": "API key removed."}}

    missing = registered_client.delete(f"/api/keys/{first_key_id}")
    assert missing.status_code == 404
    assert missing.json()["message"]["code"] == "api_key_not_found"

    revoked = registered_client.post(
        "/v1/chat/completions",
        headers={"Authorization": f"Bearer {first_key}"},
        json={"model": "mock-echo-1", "messages": [{"role": "user", "content": "Hello"}]},
    )
    assert revoked.status_code == 401
    assert revoked.json()["message"]["code"] == "invalid_api_key"

    remaining = registered_client.get("/api/me").json()["message"]["keys"]
    assert [key["id"] for key in remaining] == [second_key_id]
    active = registered_client.post(
        "/v1/chat/completions",
        headers={"Authorization": f"Bearer {second_key}"},
        json={"model": "mock-echo-1", "messages": [{"role": "user", "content": "Hello"}]},
    )
    assert active.status_code == 200


def test_logout_invalidates_session(registered_client: TestClient) -> None:
    response = registered_client.post("/api/logout")
    assert response.status_code == 200
    assert registered_client.get("/api/me").status_code == 401
