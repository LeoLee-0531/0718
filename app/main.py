import os
import sqlite3
import time
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, Any

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.database import Database
from app.schemas import ApiKeyName, ChatCompletionRequest, Credentials, LoginCredentials
from app.security import (
    SESSION_COOKIE,
    create_api_key,
    create_session_token,
    digest,
    password_hash,
    read_cookie,
)

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "public"


def json_response(
    status_code: int,
    success: bool,
    message: dict[str, Any],
    **extra: Any,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"success": success, "message": message, **extra},
    )


def error(status_code: int, code: str, detail: str) -> JSONResponse:
    return json_response(status_code, False, {"code": code, "detail": detail})


def iso_timestamp(value: int | None) -> str | None:
    if value is None:
        return None
    return datetime.fromtimestamp(value / 1000, tz=UTC).isoformat().replace("+00:00", "Z")


def approximate_tokens(text: str) -> int:
    if not text:
        return 0
    return max(1, (len(text.encode("utf-8")) + 3) // 4)


def create_app(
    database_path: str | None = None,
    session_ttl_ms: int | None = None,
    production: bool | None = None,
) -> FastAPI:
    db = Database(database_path or os.getenv("DATABASE_PATH", "data/app.db"))
    ttl = session_ttl_ms or int(os.getenv("SESSION_TTL_MS", "86400000"))
    secure_cookies = (
        production if production is not None else os.getenv("ENVIRONMENT") == "production"
    )

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        yield
        application.state.db.close()

    application = FastAPI(title="LLM Inference Service", lifespan=lifespan)
    application.state.db = db
    application.mount("/static", StaticFiles(directory=PUBLIC), name="static")

    @application.exception_handler(RequestValidationError)
    async def validation_error_handler(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        fields = [
            {"field": ".".join(str(part) for part in item["loc"][1:]), "detail": item["msg"]}
            for item in exc.errors()
        ]
        return error(400, "invalid_request", f"Request validation failed: {fields}")

    @application.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
        print(f"Unhandled request error: {request.method} {request.url.path}: {exc!r}")
        return error(500, "internal_error", "An unexpected error occurred.")

    def current_user(request: Request) -> dict[str, Any] | None:
        token = read_cookie(request.headers.get("cookie"), SESSION_COOKIE)
        if not token:
            return None
        now = int(time.time() * 1000)
        session = db.fetch_one(
            """
            SELECT users.id, users.username, sessions.expires_at
            FROM sessions
            JOIN users ON users.id = sessions.user_id
            WHERE sessions.token_hash = ?
            """,
            (digest(token),),
        )
        if not session or session["expires_at"] <= now:
            if session:
                db.execute("DELETE FROM sessions WHERE token_hash = ?", (digest(token),))
            return None
        return {"id": session["id"], "username": session["username"]}

    def require_user(request: Request) -> dict[str, Any] | JSONResponse:
        user = current_user(request)
        return user or error(401, "unauthorized", "Please sign in to continue.")

    SessionUser = Annotated[dict[str, Any] | JSONResponse, Depends(require_user)]

    @application.get("/", include_in_schema=False)
    async def home() -> FileResponse:
        return FileResponse(PUBLIC / "index.html")

    @application.get("/manual", include_in_schema=False)
    async def manual() -> FileResponse:
        return FileResponse(PUBLIC / "manual.html")

    @application.post("/api/register", status_code=201)
    async def register(credentials: Credentials) -> JSONResponse:
        hashed_password = password_hash.hash(credentials.password)
        try:
            db.execute(
                "INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)",
                (credentials.username, hashed_password, int(time.time() * 1000)),
            )
        except sqlite3.IntegrityError:
            return error(409, "username_exists", "That username is already registered.")
        return json_response(201, True, {"detail": "Account created."})

    @application.post("/api/login")
    async def login(credentials: LoginCredentials) -> JSONResponse:
        user = db.fetch_one(
            "SELECT id, username, password_hash FROM users WHERE username = ?",
            (credentials.username,),
        )
        valid = bool(user) and password_hash.verify(credentials.password, user["password_hash"])
        if not valid:
            return error(401, "invalid_credentials", "Invalid username or password.")

        token = create_session_token()
        now = int(time.time() * 1000)
        db.execute("DELETE FROM sessions WHERE expires_at <= ?", (now,))
        db.execute(
            """
            INSERT INTO sessions (token_hash, user_id, expires_at, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (digest(token), user["id"], now + ttl, now),
        )
        response = json_response(200, True, {"username": user["username"]})
        response.set_cookie(
            SESSION_COOKIE,
            token,
            max_age=ttl // 1000,
            httponly=True,
            secure=secure_cookies,
            samesite="lax",
            path="/",
        )
        return response

    @application.post("/api/logout")
    async def logout(request: Request, user: SessionUser) -> JSONResponse:
        if isinstance(user, JSONResponse):
            return user
        token = read_cookie(request.headers.get("cookie"), SESSION_COOKIE)
        if token:
            db.execute("DELETE FROM sessions WHERE token_hash = ?", (digest(token),))
        response = json_response(200, True, {"detail": "Signed out."})
        response.delete_cookie(SESSION_COOKIE, path="/", samesite="lax")
        return response

    @application.get("/api/me")
    async def me(user: SessionUser) -> JSONResponse:
        if isinstance(user, JSONResponse):
            return user
        rows = db.fetch_all(
            """
            SELECT id, name, key_prefix, created_at, last_used_at,
                   request_count, prompt_tokens, completion_tokens
            FROM api_keys WHERE user_id = ? ORDER BY created_at DESC
            """,
            (user["id"],),
        )
        keys = [
            {
                "id": row["id"],
                "name": row["name"],
                "display": f"{row['key_prefix']}...",
                "created_at": iso_timestamp(row["created_at"]),
                "last_used_at": iso_timestamp(row["last_used_at"]),
                "usage": {
                    "requests": row["request_count"],
                    "prompt_tokens": row["prompt_tokens"],
                    "completion_tokens": row["completion_tokens"],
                    "total_tokens": row["prompt_tokens"] + row["completion_tokens"],
                },
            }
            for row in rows
        ]
        return json_response(200, True, {"username": user["username"], "keys": keys})

    @application.post("/api/keys")
    async def create_key(user: SessionUser, payload: ApiKeyName | None = None) -> JSONResponse:
        if isinstance(user, JSONResponse):
            return user
        api_key = create_api_key()
        db.execute(
            """
            INSERT INTO api_keys (key_hash, name, key_prefix, user_id, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                digest(api_key),
                payload.name if payload else "Untitled key",
                api_key[:17],
                user["id"],
                int(time.time() * 1000),
            ),
        )
        return json_response(200, True, {"api_key": api_key})

    @application.patch("/api/keys/{key_id}")
    async def update_key(key_id: int, payload: ApiKeyName, user: SessionUser) -> JSONResponse:
        if isinstance(user, JSONResponse):
            return user
        cursor = db.execute(
            "UPDATE api_keys SET name = ? WHERE id = ? AND user_id = ?",
            (payload.name, key_id, user["id"]),
        )
        if cursor.rowcount == 0:
            return error(404, "api_key_not_found", "API key not found.")
        return json_response(200, True, {"name": payload.name})

    @application.delete("/api/keys/{key_id}")
    async def delete_key(key_id: int, user: SessionUser) -> JSONResponse:
        if isinstance(user, JSONResponse):
            return user
        cursor = db.execute(
            "DELETE FROM api_keys WHERE id = ? AND user_id = ?",
            (key_id, user["id"]),
        )
        if cursor.rowcount == 0:
            return error(404, "api_key_not_found", "API key not found.")
        return json_response(200, True, {"detail": "API key removed."})

    @application.post("/v1/chat/completions")
    async def chat_completions(request: Request, payload: ChatCompletionRequest) -> JSONResponse:
        authorization = request.headers.get("authorization", "")
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() != "bearer" or not token or " " in token:
            return error(401, "invalid_api_key", "A valid Bearer API key is required.")
        key = db.fetch_one("SELECT id FROM api_keys WHERE key_hash = ?", (digest(token),))
        if not key:
            return error(401, "invalid_api_key", "A valid Bearer API key is required.")

        last_user_message = next(
            (item for item in reversed(payload.messages) if item.role == "user"), None
        )
        if not last_user_message:
            return error(400, "invalid_request", "Messages must include at least one user message.")

        now = int(time.time() * 1000)
        content = f"Echo: {last_user_message.content}"
        prompt_tokens = sum(approximate_tokens(item.content) for item in payload.messages)
        completion_tokens = approximate_tokens(content)
        db.execute(
            """
            UPDATE api_keys
            SET last_used_at = ?,
                request_count = request_count + 1,
                prompt_tokens = prompt_tokens + ?,
                completion_tokens = completion_tokens + ?
            WHERE id = ?
            """,
            (now, prompt_tokens, completion_tokens, key["id"]),
        )
        return json_response(
            200,
            True,
            {},
            id=f"chatcmpl_{uuid.uuid4().hex}",
            object="chat.completion",
            created=now // 1000,
            model=payload.model,
            choices=[
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": content},
                    "finish_reason": "stop",
                }
            ],
            usage={
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
            },
        )

    @application.api_route("/api/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
    @application.api_route("/v1/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
    async def api_not_found(path: str) -> JSONResponse:
        return error(404, "not_found", f"API route not found: {path}")

    return application


app = create_app()
