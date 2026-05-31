from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from hashlib import sha256
import json
from pathlib import Path
import sqlite3

from app.memory.store import compute_repo_key


PATCH_DIR = ".repopilot"
PATCH_DB = "patches.sqlite3"
PATCH_STATUS_PENDING = "pending"
PATCH_STATUS_APPLIED = "applied"
PATCH_STATUS_FAILED = "failed"
PATCH_STATUS_EXPIRED = "expired"
DEFAULT_TTL_HOURS = 24


@dataclass(frozen=True)
class PendingPatch:
    patch_id: str
    user_id: str
    repo_key: str
    status: str
    target_files: list[str]
    diff_text: str
    diff_hash: str
    summary: str
    created_at: datetime
    updated_at: datetime
    expires_at: datetime


class SQLitePatchStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._ensure_schema()

    @classmethod
    def for_repo(cls, repo_path: str | Path) -> "SQLitePatchStore":
        root = Path(repo_path)
        patch_dir = root / PATCH_DIR
        patch_dir.mkdir(parents=True, exist_ok=True)
        return cls(patch_dir / PATCH_DB)

    def create_pending_patch(
        self,
        *,
        user_id: str,
        repo_key: str,
        target_files: list[str],
        diff_text: str,
        summary: str,
        expires_at: datetime | None = None,
    ) -> PendingPatch:
        now = _utc_now()
        expires = expires_at or now + timedelta(hours=DEFAULT_TTL_HOURS)
        diff_hash = hash_diff(diff_text)
        patch_id = _new_patch_id(user_id, repo_key, diff_hash, now)
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO patches
                    (patch_id, user_id, repo_key, status, target_files, diff_text,
                     diff_hash, summary, created_at, updated_at, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    patch_id,
                    user_id,
                    repo_key,
                    PATCH_STATUS_PENDING,
                    json.dumps(target_files, ensure_ascii=True),
                    diff_text,
                    diff_hash,
                    summary,
                    _dump_dt(now),
                    _dump_dt(now),
                    _dump_dt(expires),
                ),
            )
        patch = self.get_patch(patch_id, user_id=user_id, repo_key=repo_key)
        if patch is None:
            raise sqlite3.Error("created patch not found")
        return patch

    def get_patch(
        self,
        patch_id: str,
        *,
        user_id: str,
        repo_key: str,
    ) -> PendingPatch | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT patch_id, user_id, repo_key, status, target_files, diff_text,
                       diff_hash, summary, created_at, updated_at, expires_at
                FROM patches
                WHERE patch_id = ? AND user_id = ? AND repo_key = ?
                """,
                (patch_id, user_id, repo_key),
            ).fetchone()
        if row is None:
            return None
        return _row_to_patch(row)

    def mark_status(self, patch_id: str, status: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE patches SET status = ?, updated_at = ? WHERE patch_id = ?",
                (status, _dump_dt(_utc_now()), patch_id),
            )

    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS patches (
                    patch_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    repo_key TEXT NOT NULL,
                    status TEXT NOT NULL,
                    target_files TEXT NOT NULL,
                    diff_text TEXT NOT NULL,
                    diff_hash TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL
                )
                """
            )

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)


def store_for_existing_repo(repo_path: str | Path) -> tuple[SQLitePatchStore, str]:
    root = Path(repo_path)
    if not root.exists() or not root.is_dir():
        raise ValueError("repo_path unavailable")
    return SQLitePatchStore.for_repo(root), compute_repo_key(root)


def hash_diff(diff_text: str) -> str:
    return sha256(diff_text.encode("utf-8")).hexdigest()


def _new_patch_id(user_id: str, repo_key: str, diff_hash: str, now: datetime) -> str:
    digest = sha256(
        f"{user_id}:{repo_key}:{diff_hash}:{_dump_dt(now)}".encode("utf-8")
    ).hexdigest()[:6]
    date = now.strftime("%Y%m%d")
    return f"patch_{date}_{digest}"


def _row_to_patch(row) -> PendingPatch:
    return PendingPatch(
        patch_id=row[0],
        user_id=row[1],
        repo_key=row[2],
        status=row[3],
        target_files=list(json.loads(row[4])),
        diff_text=row[5],
        diff_hash=row[6],
        summary=row[7],
        created_at=_load_dt(row[8]),
        updated_at=_load_dt(row[9]),
        expires_at=_load_dt(row[10]),
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
