from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
import sqlite3
from uuid import uuid4

from app.memory.store import MEMORY_DIR


LOCK_DB = "mutation_locks.sqlite3"


@dataclass(frozen=True)
class RepoMutationLock:
    repo_key: str
    operation: str
    owner_token: str
    acquired: bool
    reason: str = ""

    def with_owner_token(self, owner_token: str) -> "RepoMutationLock":
        return RepoMutationLock(
            repo_key=self.repo_key,
            operation=self.operation,
            owner_token=owner_token,
            acquired=self.acquired,
            reason=self.reason,
        )


class RepoMutationLockStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._ensure_schema()

    @classmethod
    def for_repo(cls, repo_path: str | Path) -> "RepoMutationLockStore":
        lock_dir = Path(repo_path) / MEMORY_DIR
        lock_dir.mkdir(parents=True, exist_ok=True)
        return cls(lock_dir / LOCK_DB)

    def acquire(self, *, repo_key: str, operation: str) -> RepoMutationLock:
        owner_token = f"lock_{uuid4().hex}"
        now = _utc_now()
        try:
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT INTO repo_mutation_locks
                        (repo_key, owner_token, operation, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (repo_key, owner_token, operation, now, now),
                )
        except sqlite3.IntegrityError:
            return RepoMutationLock(
                repo_key=repo_key,
                operation=operation,
                owner_token="",
                acquired=False,
                reason="lock_conflict",
            )
        except sqlite3.Error:
            return RepoMutationLock(
                repo_key=repo_key,
                operation=operation,
                owner_token="",
                acquired=False,
                reason="lock_unavailable",
            )
        return RepoMutationLock(
            repo_key=repo_key,
            operation=operation,
            owner_token=owner_token,
            acquired=True,
        )

    def release(self, lock: RepoMutationLock) -> bool:
        if not lock.acquired or not lock.owner_token:
            return False
        try:
            with self._connect() as conn:
                cursor = conn.execute(
                    """
                    DELETE FROM repo_mutation_locks
                    WHERE repo_key = ? AND owner_token = ?
                    """,
                    (lock.repo_key, lock.owner_token),
                )
        except sqlite3.Error:
            return False
        return cursor.rowcount == 1

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _ensure_schema(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS repo_mutation_locks (
                    repo_key TEXT PRIMARY KEY,
                    owner_token TEXT NOT NULL,
                    operation TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()
