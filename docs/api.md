# HTTP API Contract

The server accepts and returns JSON for API routes. Error responses never
contain HTML or stack traces.

Except for the OpenAI-compatible inference response, responses use:

```json
{
  "success": true,
  "message": {}
}
```

For failures, `success` is `false` and `message` is an object containing a
stable `code` and a human-readable `detail`.

## `POST /api/register`

Request:

```json
{"username":"alice","password":"correct-horse-battery-staple"}
```

Returns `201` when the account is created. A duplicate username returns `409`.
Usernames must be 3-64 characters and contain only letters, numbers, `_`, `-`,
or `.`. Passwords must be at least 8 and at most 128 characters.

## `POST /api/login`

Request:

```json
{"username":"alice","password":"correct-horse-battery-staple"}
```

Returns `200` and a `Set-Cookie` header when credentials are valid. Invalid
credentials return `401` without identifying whether the user exists.

## `POST /api/logout`

Requires a session. Deletes the server-side session and clears the cookie.

## `GET /api/me`

Requires a session. Returns the signed-in username and masked key metadata for
rendering the account page. Each key includes usage accumulated from successful
inference requests:

```json
{
  "success": true,
  "message": {
    "username": "alice",
    "keys": [{
      "id": 1,
      "name": "Production",
      "display": "llm_live_example...",
      "created_at": "2026-07-18T08:00:00Z",
      "last_used_at": "2026-07-18T08:05:00Z",
      "usage": {
        "requests": 2,
        "prompt_tokens": 8,
        "completion_tokens": 10,
        "total_tokens": 18
      }
    }]
  }
}
```

Usage starts at zero, is tracked separately for each key, and increments only
when `POST /v1/chat/completions` returns a successful completion.

## `POST /api/keys`

Requires a session. An optional JSON body assigns a display name:

```json
{"name":"Production"}
```

Names are trimmed and must contain 1-64 characters. Omitting the body keeps
existing clients compatible and uses `Untitled key`. Returns `200` with the
newly generated key:

```json
{
  "success": true,
  "message": {"api_key":"llm_live_..."}
}
```

The complete value is shown only in this response. Creating a new key does not
invalidate older keys in the MVP.

## `PATCH /api/keys/{key_id}`

Requires a session. Updates the display name of the signed-in user's key:

```json
{"name":"Staging"}
```

Returns `200` with the normalized name. A key that does not exist or belongs to
another user returns `404` with `api_key_not_found`, matching removal behavior.

## `DELETE /api/keys/{key_id}`

Requires a session. Removes the signed-in user's API key and returns `200`:

```json
{
  "success": true,
  "message": {"detail":"API key removed."}
}
```

The removed key stops authorizing inference requests immediately. A key that
does not exist or belongs to another user returns `404` with the stable error
code `api_key_not_found`; the response does not reveal whether another user
owns the requested key.

## `POST /v1/chat/completions`

Authentication uses `Authorization: Bearer <api-key>`.

Request:

```json
{
  "model": "mock-echo-1",
  "messages": [
    {"role": "user", "content": "Hello"}
  ]
}
```

The response follows the OpenAI chat completion shape. `choices` and `usage`
remain top-level for client compatibility; `success` and `message` are also
included to satisfy the service-wide response convention.

```json
{
  "success": true,
  "message": {},
  "id": "chatcmpl_...",
  "object": "chat.completion",
  "created": 1750000000,
  "model": "mock-echo-1",
  "choices": [{
    "index": 0,
    "message": {"role": "assistant", "content": "Echo: Hello"},
    "finish_reason": "stop"
  }],
  "usage": {
    "prompt_tokens": 1,
    "completion_tokens": 2,
    "total_tokens": 3
  }
}
```

Token counts are deterministic approximations based on UTF-8 content length;
`total_tokens` always equals prompt plus completion tokens. Missing or invalid
credentials return JSON with status `401`. Malformed payloads return `400`.

