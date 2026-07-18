# Security Notes

## Credentials

- Passwords are hashed with Argon2 using `pwdlib`'s recommended parameters.
- API keys contain 32 random bytes and use the `llm_live_` prefix.
- Only SHA-256 API key digests are stored. A database leak does not expose
  directly usable keys.
- API key rename and removal operations are scoped to the authenticated owner.
  Removed keys are deleted from persistence and stop authorizing inference
  requests immediately.
- Rename or removal requests for missing keys and keys owned by another account
  use the same response so key ownership is not disclosed.
- Per-key usage monitoring stores request and token counters plus the last-used
  timestamp. It does not store prompt or completion content.
- API key names are non-secret display metadata, limited to 64 characters, and
  returned only to the authenticated owner. Clients should not put credentials
  or other secrets in a key name.
- The browser console shows a newly created complete key in a dedicated dialog
  and removes the value from the DOM when that dialog closes.
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
