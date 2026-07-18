# Product and Architecture

## MVP scope

The application lets a customer register and sign in through a browser,
create API keys, and use those keys to call an OpenAI-compatible mock chat
completion endpoint. The mock endpoint does not call a real model.

## Components

- FastAPI serves the HTML pages and JSON API from one process.
- SQLite persists users, server-side sessions, and API key hashes.
- Passwords are hashed with Argon2 before persistence.
- API keys are generated with a cryptographically secure random source. Only
  a SHA-256 digest and a short display prefix are persisted.
- Session cookies are `HttpOnly` and `SameSite=Lax`; production cookies are
  also `Secure`.

## Main flow

1. A visitor registers with a username and password.
2. The visitor signs in and receives a server-side session cookie.
3. The signed-in user creates an API key. The complete key is returned once.
4. The client sends the key as `Authorization: Bearer <api-key>` to
   `POST /v1/chat/completions`.
5. The service validates the key and returns a deterministic echo completion.

## Persistence

SQLite is accessed through Python's standard library and used for the MVP so
local development needs no external service.
The database file defaults to `data/app.db` and can be replaced with an
in-memory database in tests.

## Out of scope

Billing, quotas, key revocation, password reset, email verification, streaming
responses, and calls to a real inference provider are intentionally outside
this MVP.
