# Troubleshooting

## Login succeeds but the API console does not appear

### Symptoms

- `POST /api/login` returns `200` with `success: true`.
- The page remains on, or returns to, the login form instead of showing the API
  key console.
- `GET /api/me` may return `200`, even though the browser does not render the
  signed-in state.

### Known cause

The account menu redesign removed the `#current-user` element from
`public/index.html`, while `public/app.js` still tried to assign its
`textContent`. The resulting `TypeError` happened after `GET /api/me` succeeded.
The old `loadAccount()` error handler caught every error and treated it as an
unauthenticated response, which hid the JavaScript failure by showing the login
form again.

The fix removes the stale DOM reference and keeps the two failure modes
separate:

- A `401` response means the session is missing or expired and shows the login
  form.
- A network, response, or rendering error shows a console-loading error and is
  also logged in the browser console.

### Quick diagnosis

1. Open the browser developer tools and submit the login form.
2. In Network, confirm `POST /api/login` returns `200` and the following
   `GET /api/me` returns `200` or `401`.
3. If `/api/me` returns `200` but the login form remains visible, check Console
   for a JavaScript exception. An error involving `null`, `textContent`,
   `classList`, or `addEventListener` usually indicates that `app.js` references
   an element ID that no longer exists in `index.html`.
4. Run the DOM contract regression test:

   ```sh
   .venv/bin/pytest tests/test_pages.py::test_browser_script_references_existing_elements -q
   ```

5. Run the complete checks after correcting the mismatch:

   ```sh
   .venv/bin/pytest -q
   .venv/bin/ruff check .
   .venv/bin/ruff format --check .
   ```

During development, start Uvicorn with the documented `--reload` option. If
Python routes or static browser assets were changed while a server without
reload was running, restart it before diagnosing the response shape. A reload
can briefly replace the worker process; retry a connection failure that occurs
at the exact moment files are saved.

Do not commit or share `cookies.txt` while testing authenticated requests. It
contains an active session credential and is intentionally ignored by Git.
