import os
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path

MEMORY_DIR = ".repopilot"
MEMORY_DB = "memory.sqlite3"


@dataclass(frozen=True)
class MemoryItem:
    kind: str
    key: str
    value: str


@dataclass(frozen=True)
class MemoryWriteResult:
    key: str
    replaced: bool


def normalize_repo_path_for_key(repo_path: str | Path) -> str:
    resolved = Path(repo_path).resolve()
    normalized = resolved.as_posix()
    if os.name == "nt":
        return normalized.lower()
    return normalized


def compute_repo_key(repo_path: str | Path) -> str:
    normalized = normalize_repo_path_for_key(repo_path)
    return sha256(normalized.encode("utf-8")).hexdigest()


class SQLiteMemoryStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._ensure_schema()

    @classmethod
    def for_repo(cls, repo_path: str | Path) -> "SQLiteMemoryStore":
        root = Path(repo_path)
        memory_dir = root / MEMORY_DIR
        memory_dir.mkdir(parents=True, exist_ok=True)
        return cls(memory_dir / MEMORY_DB)

    def upsert(
        self,
        *,
        kind: str,
        user_id: str,
        repo_key: str | None,
        session_id: str | None,
        key: str,
        value: str,
    ) -> MemoryWriteResult:
        scope = _scope_for_kind(kind)
        existing = self._find_by_key(
            kind=kind,
            user_id=user_id,
            repo_key=repo_key,
            session_id=session_id,
            key=key,
        )
        now = _utc_now()
        with self._connect() as conn:
            if existing:
                conn.execute(
                    """
                    UPDATE memories
                    SET value = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (value, now, existing),
                )
                return MemoryWriteResult(key=key, replaced=True)
            conn.execute(
                """
                INSERT INTO memories
                    (kind, scope, user_id, repo_key, session_id, key, value, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (kind, scope, user_id, repo_key, session_id, key, value, now, now),
            )
        return MemoryWriteResult(key=key, replaced=False)

    def list(
        self,
        *,
        kind: str,
        user_id: str,
        repo_key: str | None,
        session_id: str | None,
    ) -> list[MemoryItem]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT kind, key, value
                FROM memories
                WHERE kind = ?
                  AND user_id = ?
                  AND COALESCE(repo_key, '') = COALESCE(?, '')
                  AND COALESCE(session_id, '') = COALESCE(?, '')
                ORDER BY updated_at DESC, key ASC
                """,
                (kind, user_id, repo_key, session_id),
            ).fetchall()
        return [MemoryItem(kind=row[0], key=row[1], value=row[2]) for row in rows]

    def delete(
        self,
        *,
        kind: str,
        user_id: str,
        repo_key: str | None,
        session_id: str | None,
        query: str,
    ) -> int:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                DELETE FROM memories
                WHERE kind = ?
                  AND user_id = ?
                  AND COALESCE(repo_key, '') = COALESCE(?, '')
                  AND COALESCE(session_id, '') = COALESCE(?, '')
                  AND key = ?
                """,
                (kind, user_id, repo_key, session_id, query),
            )
            if cursor.rowcount:
                return int(cursor.rowcount)
            cursor = conn.execute(
                """
                DELETE FROM memories
                WHERE kind = ?
                  AND user_id = ?
                  AND COALESCE(repo_key, '') = COALESCE(?, '')
                  AND COALESCE(session_id, '') = COALESCE(?, '')
                  AND value LIKE ?
                """,
                (kind, user_id, repo_key, session_id, f"%{query}%"),
            )
            return int(cursor.rowcount)

    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    kind TEXT NOT NULL,
                    scope TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    repo_key TEXT,
                    session_id TEXT,
                    key TEXT NOT NULL,
                    value TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(kind, user_id, repo_key, session_id, key)
                )
                """
            )

    def _find_by_key(
        self,
        *,
        kind: str,
        user_id: str,
        repo_key: str | None,
        session_id: str | None,
        key: str,
    ) -> int | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT id
                FROM memories
                WHERE kind = ?
                  AND user_id = ?
                  AND COALESCE(repo_key, '') = COALESCE(?, '')
                  AND COALESCE(session_id, '') = COALESCE(?, '')
                  AND key = ?
                """,
                (kind, user_id, repo_key, session_id, key),
            ).fetchone()
        if row is None:
            return None
        return int(row[0])

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)


class InMemorySessionMemoryStore:
    def __init__(self) -> None:
        self._items: dict[tuple[str, str, str], MemoryItem] = {}

    def upsert(
        self,
        *,
        user_id: str,
        session_id: str,
        key: str,
        value: str,
    ) -> MemoryWriteResult:
        storage_key = (user_id, session_id, key)
        replaced = storage_key in self._items
        self._items[storage_key] = MemoryItem(kind="STM", key=key, value=value)
        return MemoryWriteResult(key=key, replaced=replaced)

    def list(self, *, user_id: str, session_id: str) -> list[MemoryItem]:
        return [
            item
            for (stored_user, stored_session, _), item in sorted(self._items.items())
            if stored_user == user_id and stored_session == session_id
        ]


def _scope_for_kind(kind: str) -> str:
    if kind == "PREF":
        return "user"
    if kind == "LTM":
        return "user_repo"
    if kind == "STM":
        return "user_session"
    raise ValueError("unsupported memory kind")


def _utc_now() -> str:
    return datetime.now(tz=UTC).isoformat(timespec="seconds")
