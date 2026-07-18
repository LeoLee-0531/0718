import hashlib
import secrets
from http.cookies import CookieError, SimpleCookie

from pwdlib import PasswordHash

SESSION_COOKIE = "llm_session"
password_hash = PasswordHash.recommended()


def digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def create_session_token() -> str:
    return secrets.token_urlsafe(32)


def create_api_key() -> str:
    return f"llm_live_{secrets.token_urlsafe(32)}"


def read_cookie(cookie_header: str | None, name: str) -> str | None:
    if not cookie_header:
        return None
    cookie = SimpleCookie()
    try:
        cookie.load(cookie_header)
    except CookieError:
        return None
    morsel = cookie.get(name)
    return morsel.value if morsel else None
