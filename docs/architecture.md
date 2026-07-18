# Product and Architecture

## MVP scope

The application lets a customer register and sign in through a browser,
create API keys, and use those keys to call an OpenAI-compatible mock chat
completion endpoint. The mock endpoint does not call a real model.

## Components

- FastAPI serves the HTML pages and JSON API from one process.
- FastAPI `StreamingResponse` serves OpenAI-compatible SSE completions when a
  request enables streaming.
- SQLite persists users, server-side sessions, and API key hashes.
- Passwords are hashed with Argon2 before persistence.
- API keys are generated with a cryptographically secure random source. Only
  a SHA-256 digest, user-defined display name, and short display prefix are
  persisted.
- Successful inference requests atomically add request and token counters to
  the API key that authorized the request. Prompt and response content is not
  stored for usage monitoring.
- Session cookies are `HttpOnly` and `SameSite=Lax`; production cookies are
  also `Secure`.

## Main flow

1. A visitor registers with a username and password. Registration returns the
   browser to the sign-in form without creating a session.
2. The visitor signs in with a separate submission, receives a server-side
   session cookie, and the browser loads `GET /api/me` before switching from
   the account form to the console.
3. The signed-in user names and creates an API key. The browser console shows
   the complete key once in a dedicated application dialog.
4. The signed-in user can rename or remove one of their API keys through
   accessible icon actions in a responsive field-based table. Narrow screens
   retain every field without horizontal page overflow. Removal requires
   confirmation in an application dialog and revokes the key immediately.
5. The client sends an active key as `Authorization: Bearer <api-key>` to
   `POST /v1/chat/completions`.
6. The service validates the key, records that key's successful request and
   token usage, and returns a deterministic echo completion.

## Persistence

SQLite is accessed through Python's standard library and used for the MVP so
local development needs no external service.
The database file defaults to `data/app.db` and can be replaced with an
in-memory database in tests.
Existing databases are migrated at startup to add the display name and missing
API key usage counters with safe defaults.

The development server uses the fixed address `http://127.0.0.1:8000` and
reloads after source changes so the Python routes and browser assets do not run
from different revisions during development.

## Source layout

- `app/` contains the FastAPI application, schemas, persistence, and security helpers.
- `public/` contains the browser console and public manual assets.
- `tests/` contains integration tests and imports the application from the repository root.

Streaming uses an asynchronous generator. It yields deterministic character
chunks without splitting Unicode code points and records per-key usage only
when the generator reaches its successful completion event.

## Out of scope

Billing, quotas, password reset, email verification, streaming responses, and
calls to a real inference provider are intentionally outside this MVP.
