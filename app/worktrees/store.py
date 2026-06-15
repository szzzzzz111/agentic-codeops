from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
import json
import sqlite3

from app.memory.store import compute_repo_key


WORKTREE_DIR = ".repopilot"
WORKTREE_DB = "worktrees.sqlite3"
WORKTREE_STATUS_READY = "ready"
WORKTREE_STATUS_CREATE_FAILED = "create_failed"
WORKTREE_STATUS_PATCH_APPLIED = "patch_applied"
WORKTREE_STATUS_PATCH_FAILED = "patch_failed"
WORKTREE_STATUS_VERIFICATION_SUCCEEDED = "verification_succeeded"
WORKTREE_STATUS_VERIFICATION_FAILED = "verification_failed"
WORKTREE_STATUS_DISPOSAL_FAILED = "disposal_failed"
WORKTREE_STATUS_DISCARDED = "discarded"


@dataclass(frozen=True)
class WorktreeRecord:
    worktree_id: str
    user_id: str
    repo_key: str
    patch_id: str
    base_commit: str
    status: str
    verification_label: str
    verification_status: str
    changed_files: list[str]
    created_at: datetime
    updated_at: datetime


class SQLiteWorktreeStore:
    def __init__(self, db_path: Path, *, initialize: bool = True) -> None:
        self.db_path = db_path
        if initialize:
            self._ensure_schema()

    @classmethod
    def for_repo(cls, repo_path: str | Path) -> tuple["SQLiteWorktreeStore", str]:
        root = Path(repo_path)
        worktree_dir = root / WORKTREE_DIR
        worktree_dir.mkdir(parents=True, exist_ok=True)
        return cls(worktree_dir / WORKTREE_DB), compute_repo_key(root)

    @classmethod
    def for_existing_repo(
        cls,
        repo_path: str | Path,
    ) -> tuple["SQLiteWorktreeStore", str] | None:
        root = Path(repo_path)
        db_path = root / WORKTREE_DIR / WORKTREE_DB
        if not db_path.exists():
            return None
        return cls(db_path, initialize=False), compute_repo_key(root)

    def create_worktree(
        self,
        *,
        user_id: str,
        repo_key: str,
        worktree_id: str,
        patch_id: str,
        base_commit: str,
        status: str,
        verification_label: str = "",
        verification_status: str = "",
        changed_files: list[str] | None = None,
    ) -> WorktreeRecord:
        now = _utc_now()
        payload = json.dumps(changed_files or [], ensure_ascii=True)
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO worktrees
                    (worktree_id, user_id, repo_key, patch_id, base_commit, status,
                     verification_label, verification_status, changed_files_json,
                     created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    worktree_id,
                    user_id,
                    repo_key,
                    patch_id,
                    base_commit,
                    status,
                    verification_label,
                    verification_status,
                    payload,
                    _dump_dt(now),
                    _dump_dt(now),
                ),
            )
        record = self.get_worktree(worktree_id, user_id=user_id, repo_key=repo_key)
        if record is None:
            raise sqlite3.Error("created worktree not found")
        return record

    def update_worktree(
        self,
        worktree_id: str,
        *,
        user_id: str,
        repo_key: str,
        status: str,
        verification_label: str | None = None,
        verification_status: str | None = None,
        changed_files: list[str] | None = None,
    ) -> bool:
        existing = self.get_worktree(worktree_id, user_id=user_id, repo_key=repo_key)
        if existing is None:
            return False
        with self._connect() as conn:
            cursor = conn.execute(
                """
                UPDATE worktrees
                SET status = ?,
                    verification_label = ?,
                    verification_status = ?,
                    changed_files_json = ?,
                    updated_at = ?
                WHERE worktree_id = ? AND user_id = ? AND repo_key = ?
                """,
                (
                    status,
                    existing.verification_label
                    if verification_label is None
                    else verification_label,
                    existing.verification_status
                    if verification_status is None
                    else verification_status,
                    json.dumps(
                        existing.changed_files if changed_files is None else changed_files,
                        ensure_ascii=True,
                    ),
                    _dump_dt(_utc_now()),
                    worktree_id,
                    user_id,
                    repo_key,
                ),
            )
        return cursor.rowcount == 1

    def get_worktree(
        self,
        worktree_id: str,
        *,
        user_id: str,
        repo_key: str,
    ) -> WorktreeRecord | None:
        with self._connect_readonly() as conn:
            row = conn.execute(
                """
                SELECT worktree_id, user_id, repo_key, patch_id, base_commit, status,
                       verification_label, verification_status, changed_files_json,
                       created_at, updated_at
                FROM worktrees
                WHERE worktree_id = ? AND user_id = ? AND repo_key = ?
                """,
                (worktree_id, user_id, repo_key),
            ).fetchone()
        if row is None:
            return None
        return _row_to_record(row)

    def list_worktrees(
        self,
        *,
        user_id: str,
        repo_key: str,
        limit: int = 20,
    ) -> list[WorktreeRecord]:
        limit = max(1, min(int(limit), 20))
        with self._connect_readonly() as conn:
            rows = conn.execute(
                """
                SELECT worktree_id, user_id, repo_key, patch_id, base_commit, status,
                       verification_label, verification_status, changed_files_json,
                       created_at, updated_at
                FROM worktrees
                WHERE user_id = ? AND repo_key = ?
                ORDER BY created_at DESC, worktree_id DESC
                LIMIT ?
                """,
                (user_id, repo_key, limit),
            ).fetchall()
        return [_row_to_record(row) for row in rows]

    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS worktrees (
                    worktree_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    repo_key TEXT NOT NULL,
                    patch_id TEXT NOT NULL,
                    base_commit TEXT NOT NULL,
                    status TEXT NOT NULL,
                    verification_label TEXT NOT NULL,
                    verification_status TEXT NOT NULL,
                    changed_files_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_worktrees_scope
                ON worktrees(user_id, repo_key, created_at)
                """
            )

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _connect_readonly(self) -> sqlite3.Connection:
        uri = f"file:{self.db_path.as_posix()}?mode=ro&immutable=1"
        return sqlite3.connect(uri, uri=True)


def _row_to_record(row) -> WorktreeRecord:
    return WorktreeRecord(
        worktree_id=row[0],
        user_id=row[1],
        repo_key=row[2],
        patch_id=row[3],
        base_commit=row[4],
        status=row[5],
        verification_label=row[6],
        verification_status=row[7],
        changed_files=list(json.loads(row[8] or "[]")),
        created_at=_load_dt(row[9]),
        updated_at=_load_dt(row[10]),
    )


def _utc_now() -> datetime:
    return datetime.now(tz=UTC)


def _dump_dt(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).isoformat(timespec="microseconds")


def _load_dt(value: str) -> datetime:
    loaded = datetime.fromisoformat(value)
    if loaded.tzinfo is None:
        return loaded.replace(tzinfo=UTC)
    return loaded.astimezone(UTC)
