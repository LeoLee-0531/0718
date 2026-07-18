import sqlite3
from pathlib import Path
from threading import Lock
from typing import Any


class Database:
    def __init__(self, path: str) -> None:
        if path != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(path, check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self._lock = Lock()
        self._initialize()

    def _initialize(self) -> None:
        with self._lock:
            self._connection.execute("PRAGMA foreign_keys = ON")
            if self._connection.execute("PRAGMA database_list").fetchone()[2]:
                self._connection.execute("PRAGMA journal_mode = WAL")
            self._connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE COLLATE NOCASE,
                    password_hash TEXT NOT NULL,
                    created_at INTEGER NOT NULL
                );

                CREATE TABLE IF NOT EXISTS sessions (
                    token_hash TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    expires_at INTEGER NOT NULL,
                    created_at INTEGER NOT NULL
                );

                CREATE INDEX IF NOT EXISTS sessions_expires_at_idx
                    ON sessions(expires_at);

                CREATE TABLE IF NOT EXISTS api_keys (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key_hash TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL DEFAULT 'Untitled key',
                    key_prefix TEXT NOT NULL,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    created_at INTEGER NOT NULL,
                    last_used_at INTEGER,
                    request_count INTEGER NOT NULL DEFAULT 0,
                    prompt_tokens INTEGER NOT NULL DEFAULT 0,
                    completion_tokens INTEGER NOT NULL DEFAULT 0
                );

                CREATE INDEX IF NOT EXISTS api_keys_user_id_idx
                    ON api_keys(user_id);
                """
            )
            api_key_columns = {
                row["name"]
                for row in self._connection.execute("PRAGMA table_info(api_keys)").fetchall()
            }
            if "name" not in api_key_columns:
                self._connection.execute(
                    "ALTER TABLE api_keys ADD COLUMN name TEXT NOT NULL DEFAULT 'Untitled key'"
                )
            if "request_count" not in api_key_columns:
                self._connection.execute(
                    "ALTER TABLE api_keys ADD COLUMN request_count INTEGER NOT NULL DEFAULT 0"
                )
            if "prompt_tokens" not in api_key_columns:
                self._connection.execute(
                    "ALTER TABLE api_keys ADD COLUMN prompt_tokens INTEGER NOT NULL DEFAULT 0"
                )
            if "completion_tokens" not in api_key_columns:
                self._connection.execute(
                    "ALTER TABLE api_keys ADD COLUMN completion_tokens INTEGER NOT NULL DEFAULT 0"
                )
            self._connection.commit()

    def execute(self, query: str, parameters: tuple[Any, ...] = ()) -> sqlite3.Cursor:
        with self._lock:
            cursor = self._connection.execute(query, parameters)
            self._connection.commit()
            return cursor

    def fetch_one(self, query: str, parameters: tuple[Any, ...] = ()) -> sqlite3.Row | None:
        with self._lock:
            return self._connection.execute(query, parameters).fetchone()

    def fetch_all(self, query: str, parameters: tuple[Any, ...] = ()) -> list[sqlite3.Row]:
        with self._lock:
            return self._connection.execute(query, parameters).fetchall()

    def close(self) -> None:
        with self._lock:
            self._connection.close()
