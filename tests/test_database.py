import sqlite3

from app.database import Database


def test_existing_api_key_rows_receive_zeroed_usage_counters(tmp_path) -> None:
    path = tmp_path / "legacy.db"
    connection = sqlite3.connect(path)
    connection.executescript(
        """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at INTEGER NOT NULL
        );
        CREATE TABLE api_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key_hash TEXT NOT NULL UNIQUE,
            key_prefix TEXT NOT NULL,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            created_at INTEGER NOT NULL,
            last_used_at INTEGER
        );
        INSERT INTO users (username, password_hash, created_at)
        VALUES ('alice', 'hashed', 1);
        INSERT INTO api_keys (key_hash, key_prefix, user_id, created_at)
        VALUES ('digest', 'llm_live_example', 1, 1);
        """
    )
    connection.commit()
    connection.close()

    database = Database(str(path))
    row = database.fetch_one(
        "SELECT name, request_count, prompt_tokens, completion_tokens FROM api_keys WHERE id = 1"
    )
    database.close()

    assert dict(row) == {
        "name": "Untitled key",
        "request_count": 0,
        "prompt_tokens": 0,
        "completion_tokens": 0,
    }
