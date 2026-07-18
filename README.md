# LLM Inference Service MVP

A small account and API key service with an OpenAI-compatible mock chat
completion endpoint.

## Requirements

- Python 3.11 or newer
- [uv](https://docs.astral.sh/uv/)

## Install

```sh
uv sync
```

## Start

```sh
uv run uvicorn app.main:app --host 127.0.0.1 --port 3000
```

The service listens on `http://localhost:3000` by default. Open `/` to create
an account or `/manual` for the public API manual.

Configuration:

| Variable | Default | Purpose |
| --- | --- | --- |
| `PORT` | `3000` | HTTP listen port |
| `HOST` | `127.0.0.1` | HTTP listen address |
| `DATABASE_PATH` | `data/app.db` | SQLite database path |
| `SESSION_TTL_MS` | `86400000` | Session lifetime in milliseconds |
| `NODE_ENV` | `development` | Enables secure cookies in production |

## Test

```sh
uv run pytest
```

The integration suite uses a temporary SQLite database and exercises account
registration, login sessions, API key creation, inference authentication,
echo responses, usage consistency, validation errors, and the public manual.

## API quick start

Register and store the login cookie:

```sh
curl -i -X POST http://localhost:3000/api/register \
  -H 'Content-Type: application/json' \
  -d '{"username":"alice","password":"correct-horse-battery-staple"}'

curl -i -c cookies.txt -X POST http://localhost:3000/api/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"alice","password":"correct-horse-battery-staple"}'
```

Create a key with the saved session:

```sh
curl -X POST http://localhost:3000/api/keys -b cookies.txt
```

Call the mock inference endpoint using the returned key:

```sh
curl -X POST http://localhost:3000/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer llm_live_REPLACE_ME' \
  -d '{"model":"mock-echo-1","messages":[{"role":"user","content":"Hello"}]}'
```

See [docs/api.md](docs/api.md) for the complete contract and `/manual` for the
browser manual.
