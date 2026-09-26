"""Per-contact conversation history in SQLite, so context survives restarts."""

import sqlite3
import threading
import time


class ConversationStore:
    def __init__(self, path: str):
        self._lock = threading.Lock()
        self._db = sqlite3.connect(path, check_same_thread=False)
        self._db.execute(
            "CREATE TABLE IF NOT EXISTS messages ("
            " id INTEGER PRIMARY KEY AUTOINCREMENT,"
            " contact TEXT NOT NULL,"
            " role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),"
            " content TEXT NOT NULL,"
            " created_at REAL NOT NULL)"
        )
        self._db.execute("CREATE INDEX IF NOT EXISTS idx_contact ON messages (contact, id)")
        self._db.execute("CREATE TABLE IF NOT EXISTS seen (message_sid TEXT PRIMARY KEY)")
        self._db.commit()

    def add(self, contact: str, role: str, content: str) -> None:
        with self._lock:
            self._db.execute(
                "INSERT INTO messages (contact, role, content, created_at) VALUES (?, ?, ?, ?)",
                (contact, role, content, time.time()),
            )
            self._db.commit()

    def history(self, contact: str, limit: int) -> list[dict]:
        """Last `limit` messages, oldest first, starting on a user turn."""
        with self._lock:
            rows = self._db.execute(
                "SELECT role, content FROM messages WHERE contact = ? ORDER BY id DESC LIMIT ?",
                (contact, limit),
            ).fetchall()
        messages = [{"role": r, "content": c} for r, c in reversed(rows)]
        while messages and messages[0]["role"] != "user":
            messages.pop(0)
        return messages

    def mark_seen(self, message_sid: str) -> bool:
        """Record a Twilio MessageSid; False if it was already handled (webhook retry)."""
        with self._lock:
            try:
                self._db.execute("INSERT INTO seen (message_sid) VALUES (?)", (message_sid,))
                self._db.commit()
                return True
            except sqlite3.IntegrityError:
                return False
