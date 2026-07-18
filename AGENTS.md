# LLM Inference Service

This repository contains the MVP for a small LLM inference service. Read the
documents below before changing behavior:

- [Product and architecture](docs/architecture.md)
- [HTTP API contract](docs/api.md)
- [Security notes](docs/security.md)
- [Development guide](README.md)

## Engineering rules

- Keep API behavior aligned with `docs/api.md` and update the document first
  when a contract changes.
- All non-inference JSON responses use `{ "success": boolean, "message": {} }`.
- The inference endpoint keeps OpenAI-compatible fields at the top level and
  also includes `success` and `message`.
- Never store plaintext passwords, plaintext API keys, or session identifiers.
- Add or update automated tests for every behavioral change.
- Commit messages use `[type]: [description]`, for example
  `feat: add account registration`.

