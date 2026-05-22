import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "bot.db"

def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.row_factory = sqlite3.Row
    return conn

def init_db() -> None:
    with _get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                user_id     INTEGER PRIMARY KEY,
                username    TEXT,
                first_name  TEXT,
                last_name   TEXT,
                first_seen  TEXT NOT NULL,
                last_seen   TEXT NOT NULL,
                task_count  INTEGER NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS tasks (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL,
                task_text   TEXT,
                result_text TEXT,
                created_at  TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            );
        """)

def upsert_user(user_id: int, username: str | None,
                first_name: str | None, last_name: str | None) -> None:
    now = datetime.utcnow().isoformat(sep=" ", timespec="seconds")
    with _get_conn() as conn:
        conn.execute("""
            INSERT INTO users (user_id, username, first_name, last_name, first_seen, last_seen)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username   = excluded.username,
                first_name = excluded.first_name,
                last_name  = excluded.last_name,
                last_seen  = excluded.last_seen
        """, (user_id, username, first_name, last_name, now, now))

def get_user(user_id: int) -> sqlite3.Row | None:
    with _get_conn() as conn:
        return conn.execute(
            "SELECT * FROM users WHERE user_id = ?", (user_id,)
        ).fetchone()


def get_all_users() -> list[sqlite3.Row]:
    with _get_conn() as conn:
        return conn.execute(
            "SELECT * FROM users ORDER BY first_seen DESC"
        ).fetchall()

def log_task(user_id: int, task_text: str, result_text: str) -> None:
    now = datetime.utcnow().isoformat(sep=" ", timespec="seconds")
    with _get_conn() as conn:
        conn.execute("""
            INSERT INTO tasks (user_id, task_text, result_text, created_at)
            VALUES (?, ?, ?, ?)
        """, (user_id, task_text[:3000], result_text[:3000], now))
        conn.execute("""
            UPDATE users SET task_count = task_count + 1, last_seen = ?
            WHERE user_id = ?
        """, (now, user_id))
