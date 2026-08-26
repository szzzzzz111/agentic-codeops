import json
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from app.memory.store import compute_repo_key

AUDIT_DIR = ".repopilot"
AUDIT_DB = "audit.sqlite3"
DEFAULT_RECENT_LIMIT = 20


@dataclass(frozen=True)
class AuditEvent:
    event_id: str
    event_type: str
    user_id: str
    repo_key: str
    session_id: str
    trace_id: str
    related_id: str
    status: str
    summary: str
    payload: dict[str, str | int | float | bool]
    created_at: str


class SQLiteAuditStore:
    def __init__(self, db_path: Path, *, initialize: bool = True) -> None:
        self.db_path = db_path
        if initialize:
            self._ensure_schema()

    @classmethod
    def for_repo(cls, repo_path: str | Path) -> tuple["SQLiteAuditStore", str]:
        root = Path(repo_path)
        audit_dir = root / AUDIT_DIR
        audit_dir.mkdir(parents=True, exist_ok=True)
        return cls(audit_dir / AUDIT_DB), compute_repo_key(root)

    @classmethod
    def for_existing_repo(
        cls,
        repo_path: str | Path,
    ) -> tuple["SQLiteAuditStore", str] | None:
        root = Path(repo_path)
        db_path = root / AUDIT_DIR / AUDIT_DB
        if not db_path.exists():
            return None
        return cls(db_path, initialize=False), compute_repo_key(root)

    def insert_event(
        self,
        *,
        event_type: str,
        user_id: str,
        repo_key: str,
        session_id: str = "",
        trace_id: str = "",
        related_id: str = "",
        status: str,
        summary: str,
        payload: dict[str, str | int | float | bool],
    ) -> AuditEvent:
        now = _utc_now()
        event_id = f"audit_{datetime.now(tz=UTC).strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:8]}"
        payload_json = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO audit_events
                    (event_id, event_type, user_id, repo_key, session_id, trace_id,
                     related_id, status, summary, payload_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    event_type,
                    user_id,
                    repo_key,
                    session_id,
                    trace_id,
                    related_id,
                    status,
                    summary,
                    payload_json,
                    now,
                ),
            )
        return AuditEvent(
            event_id=event_id,
            event_type=event_type,
            user_id=user_id,
            repo_key=repo_key,
            session_id=session_id,
            trace_id=trace_id,
            related_id=related_id,
            status=status,
            summary=summary,
            payload=payload,
            created_at=now,
        )

    def recent_events(
        self,
        *,
        user_id: str,
        repo_key: str,
        limit: int = DEFAULT_RECENT_LIMIT,
        event_type: str | None = None,
    ) -> list[AuditEvent]:
        limit = max(1, min(int(limit), 100))
        where = "WHERE user_id = ? AND repo_key = ?"
        params: list[str | int] = [user_id, repo_key]
        if event_type:
            where += " AND event_type = ?"
            params.append(event_type)
        params.append(limit)
        with self._connect_readonly() as conn:
            rows = conn.execute(
                f"""
                SELECT event_id, event_type, user_id, repo_key, session_id, trace_id,
                       related_id, status, summary, payload_json, created_at
                FROM audit_events
                {where}
                ORDER BY created_at DESC, event_id DESC
                LIMIT ?
                """,
                tuple(params),
            ).fetchall()
        return [_event_from_row(row) for row in rows]

    def find_by_trace_or_related_id(
        self,
        *,
        user_id: str,
        repo_key: str,
        identifier: str,
        limit: int = DEFAULT_RECENT_LIMIT,
    ) -> list[AuditEvent]:
        with self._connect_readonly() as conn:
            rows = conn.execute(
                """
                SELECT event_id, event_type, user_id, repo_key, session_id, trace_id,
                       related_id, status, summary, payload_json, created_at
                FROM audit_events
                WHERE user_id = ?
                  AND repo_key = ?
                  AND (trace_id = ? OR related_id = ? OR event_id = ?)
                ORDER BY created_at DESC, event_id DESC
                LIMIT ?
                """,
                (user_id, repo_key, identifier, identifier, identifier, limit),
            ).fetchall()
        return [_event_from_row(row) for row in rows]

    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_events (
                    event_id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    repo_key TEXT NOT NULL,
                    session_id TEXT,
                    trace_id TEXT,
                    related_id TEXT,
                    status TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_audit_scope_created
                ON audit_events(user_id, repo_key, created_at)
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_audit_trace
                ON audit_events(user_id, repo_key, trace_id)
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_audit_related
                ON audit_events(user_id, repo_key, related_id)
                """
            )

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _connect_readonly(self) -> sqlite3.Connection:
        uri = f"file:{self.db_path.as_posix()}?mode=ro"
        return sqlite3.connect(uri, uri=True)


def _event_from_row(row) -> AuditEvent:
    return AuditEvent(
        event_id=row[0],
        event_type=row[1],
        user_id=row[2],
        repo_key=row[3],
        session_id=row[4] or "",
        trace_id=row[5] or "",
        related_id=row[6] or "",
        status=row[7],
        summary=row[8],
        payload=json.loads(row[9] or "{}"),
        created_at=row[10],
    )


def _utc_now() -> str:
    return datetime.now(tz=UTC).isoformat(timespec="seconds")
