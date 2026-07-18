# Security Notes

## Credentials

- Passwords are hashed with Argon2 using `pwdlib`'s recommended parameters.
- API keys contain 32 random bytes and use the `llm_live_` prefix.
- Only SHA-256 API key digests are stored. A database leak does not expose
  directly usable keys.
- Login errors deliberately do not reveal whether a username exists.

## Sessions

- Session identifiers contain 32 random bytes.
- Only SHA-256 session digests are stored.
- Cookies are `HttpOnly`, `SameSite=Lax`, and use a configurable lifetime.
- `Secure` is enabled when `ENVIRONMENT=production`.
- Local curl cookie jars contain active session credentials. `cookies.txt` is
  ignored by Git and must never be committed or shared.

## Deployment requirements

Terminate TLS before exposing the service publicly. Set a private writable
`DATABASE_PATH`, run as an unprivileged user, back up the database, and add
rate limiting before a public production launch. The MVP does not include
distributed sessions or abuse prevention.
