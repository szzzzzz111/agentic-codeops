from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
import sqlite3

from app.longtask.types import (
    DEFAULT_LIST_LIMIT,
    MAX_OPEN_TASKS,
    LongTask,
    LongTaskStep,
    TASK_STATUS_FAILED,
    TASK_STATUS_PAUSED,
    TERMINAL_STATUSES,
)
from app.memory.store import compute_repo_key


LONGTASK_DIR = ".repopilot"
LONGTASK_DB = "tasks.sqlite3"


class SQLiteLongTaskStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._ensure_schema()

    @classmethod
    def for_repo(cls, repo_path: str | Path) -> "SQLiteLongTaskStore":
        root = Path(repo_path)
        task_dir = root / LONGTASK_DIR
        task_dir.mkdir(parents=True, exist_ok=True)
        return cls(task_dir / LONGTASK_DB)

    def create_task(
        self,
        *,
        user_id: str,
        repo_key: str,
        title: str,
        goal: str,
        task_type: str,
        plan_source: str,
        steps: list[LongTaskStep | dict[str, str]],
    ) -> LongTask:
        now = _utc_now()
        task_id = _new_task_id(user_id, repo_key, goal, now)
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO long_tasks
                    (task_id, user_id, repo_key, title, goal, task_type, status,
                     plan_source, current_step_index, retry_round, archived,
                     created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, 'paused', ?, 0, 0, 0, ?, ?)
                """,
                (
                    task_id,
                    user_id,
                    repo_key,
                    _limit(title, 120),
                    _limit(goal, 4000),
                    task_type,
                    plan_source,
                    now,
                    now,
                ),
            )
            for position, step in enumerate(steps):
                normalized = _coerce_step(step)
                conn.execute(
                    """
                    INSERT INTO long_task_steps
                        (task_id, step_id, position, title, action_type, query_hint,
                         status, attempt_count, retry_round, expected_outcome,
                         acceptance_hint, thought_summary, action_summary,
                         observation_summary, trace_status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, '', '', '', '')
                    """,
                    (
                        task_id,
                        normalized.step_id,
                        position,
                        normalized.title,
                        normalized.action_type,
                        normalized.query_hint,
                        normalized.status,
                        normalized.attempt_count,
                        normalized.retry_round,
                        normalized.expected_outcome,
                        normalized.acceptance_hint,
                    ),
                )
        task = self.get_task(task_id)
        if task is None:
            raise sqlite3.Error("created task not found")
        return task

    def get_task(self, task_id: str) -> LongTask | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT task_id, user_id, repo_key, title, goal, task_type, status,
                       plan_source, current_step_index, retry_round, archived
                FROM long_tasks
                WHERE task_id = ?
                """,
                (task_id,),
            ).fetchone()
            if row is None:
                return None
            steps = conn.execute(
                """
                SELECT step_id, title, action_type, query_hint, status, attempt_count,
                       retry_round, expected_outcome, acceptance_hint, thought_summary,
                       action_summary, observation_summary, trace_status
                FROM long_task_steps
                WHERE task_id = ?
                ORDER BY position ASC
                """,
                (task_id,),
            ).fetchall()
        return LongTask(
            task_id=row[0],
            user_id=row[1],
            repo_key=row[2],
            title=row[3],
            goal=row[4],
            task_type=row[5],
            status=row[6],
            plan_source=row[7],
            current_step_index=int(row[8]),
            retry_round=int(row[9]),
            archived=bool(row[10]),
            steps=[
                LongTaskStep(
                    step_id=step[0],
                    title=step[1],
                    action_type=step[2],
                    query_hint=step[3],
                    status=step[4],
                    attempt_count=int(step[5]),
                    retry_round=int(step[6]),
                    expected_outcome=step[7],
                    acceptance_hint=step[8],
                    thought_summary=step[9],
                    action_summary=step[10],
                    observation_summary=step[11],
                    trace_status=step[12],
                )
                for step in steps
            ],
        )

    def list_tasks(
        self,
        *,
        user_id: str,
        repo_key: str,
        limit: int = DEFAULT_LIST_LIMIT,
    ) -> list[LongTask]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT task_id
                FROM long_tasks
                WHERE user_id = ? AND repo_key = ? AND archived = 0
                ORDER BY updated_at DESC, created_at DESC
                LIMIT ?
                """,
                (user_id, repo_key, limit),
            ).fetchall()
        return [task for row in rows if (task := self.get_task(row[0])) is not None]

    def count_open_tasks(self, *, user_id: str, repo_key: str) -> int:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT COUNT(*)
                FROM long_tasks
                WHERE user_id = ? AND repo_key = ? AND archived = 0
                """,
                (user_id, repo_key),
            ).fetchone()
        return int(row[0])

    def can_create_task(self, *, user_id: str, repo_key: str) -> bool:
        return self.count_open_tasks(user_id=user_id, repo_key=repo_key) < MAX_OPEN_TASKS

    def update_task_status(self, task_id: str, status: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE long_tasks SET status = ?, updated_at = ? WHERE task_id = ?",
                (status, _utc_now(), task_id),
            )

    def append_scratch(self, task_id: str, content: str) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO long_task_scratch (task_id, content, created_at)
                VALUES (?, ?, ?)
                """,
                (task_id, _limit(content, 4000), _utc_now()),
            )

    def archive_task(self, task_id: str) -> bool:
        task = self.get_task(task_id)
        if task is None or task.status not in TERMINAL_STATUSES:
            return False
        with self._connect() as conn:
            conn.execute(
                "UPDATE long_tasks SET archived = 1, updated_at = ? WHERE task_id = ?",
                (_utc_now(), task_id),
            )
        return True

    def reopen_failed_task(self, task_id: str) -> LongTask | None:
        task = self.get_task(task_id)
        if task is None or task.status != TASK_STATUS_FAILED or task.archived:
            return None
        retry_round = task.retry_round + 1
        current = task.current_step
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE long_tasks
                SET status = ?, retry_round = ?, updated_at = ?
                WHERE task_id = ?
                """,
                (TASK_STATUS_PAUSED, retry_round, _utc_now(), task_id),
            )
            if current is not None:
                conn.execute(
                    """
                    UPDATE long_task_steps
                    SET status = ?, attempt_count = 0, retry_round = ?
                    WHERE task_id = ? AND step_id = ?
                    """,
                    (TASK_STATUS_PAUSED, retry_round, task_id, current.step_id),
                )
        return self.get_task(task_id)

    def mark_step_success(self, task: LongTask, observation_summary: str) -> LongTask:
        current = task.current_step
        if current is None:
            return task
        is_last = task.current_step_index >= len(task.steps) - 1
        new_task_status = "completed" if is_last else "paused"
        next_index = task.current_step_index if is_last else task.current_step_index + 1
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE long_task_steps
                SET status = 'completed', thought_summary = ?, action_summary = ?,
                    observation_summary = ?, trace_status = 'success'
                WHERE task_id = ? AND step_id = ?
                """,
                (
                    _limit(f"执行步骤：{current.title}", 1000),
                    current.action_type,
                    _limit(observation_summary, 1000),
                    task.task_id,
                    current.step_id,
                ),
            )
            conn.execute(
                """
                UPDATE long_tasks
                SET status = ?, current_step_index = ?, updated_at = ?
                WHERE task_id = ?
                """,
                (new_task_status, next_index, _utc_now(), task.task_id),
            )
        return self.get_task(task.task_id)

    def mark_step_blocked(self, task: LongTask, observation_summary: str) -> LongTask:
        current = task.current_step
        if current is None:
            return task
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE long_task_steps
                SET status = 'blocked', observation_summary = ?, trace_status = 'blocked'
                WHERE task_id = ? AND step_id = ?
                """,
                (_limit(observation_summary, 1000), task.task_id, current.step_id),
            )
            conn.execute(
                """
                UPDATE long_tasks
                SET status = 'blocked', updated_at = ?
                WHERE task_id = ?
                """,
                (_utc_now(), task.task_id),
            )
        return self.get_task(task.task_id)

    def mark_step_failure(self, task: LongTask, error_summary: str) -> LongTask:
        current = task.current_step
        if current is None:
            return task
        attempt_count = current.attempt_count + 1
        task_status = "failed" if attempt_count >= 3 else "paused"
        step_status = "failed" if task_status == "failed" else "paused"
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE long_task_steps
                SET status = ?, attempt_count = ?, observation_summary = ?,
                    trace_status = 'error'
                WHERE task_id = ? AND step_id = ?
                """,
                (
                    step_status,
                    attempt_count,
                    _limit(error_summary, 1000),
                    task.task_id,
                    current.step_id,
                ),
            )
            conn.execute(
                "UPDATE long_tasks SET status = ?, updated_at = ? WHERE task_id = ?",
                (task_status, _utc_now(), task.task_id),
            )
        return self.get_task(task.task_id)

    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS long_tasks (
                    task_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    repo_key TEXT NOT NULL,
                    title TEXT NOT NULL,
                    goal TEXT NOT NULL,
                    task_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    plan_source TEXT NOT NULL,
                    current_step_index INTEGER NOT NULL,
                    retry_round INTEGER NOT NULL,
                    archived INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS long_task_steps (
                    task_id TEXT NOT NULL,
                    step_id TEXT NOT NULL,
                    position INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    action_type TEXT NOT NULL,
                    query_hint TEXT NOT NULL,
                    status TEXT NOT NULL,
                    attempt_count INTEGER NOT NULL,
                    retry_round INTEGER NOT NULL,
                    expected_outcome TEXT NOT NULL,
                    acceptance_hint TEXT NOT NULL,
                    thought_summary TEXT NOT NULL,
                    action_summary TEXT NOT NULL,
                    observation_summary TEXT NOT NULL,
                    trace_status TEXT NOT NULL,
                    PRIMARY KEY (task_id, step_id)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS long_task_scratch (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)


def store_for_existing_repo(repo_path: str | Path) -> tuple[SQLiteLongTaskStore, str]:
    root = Path(repo_path)
    if not root.exists() or not root.is_dir():
        raise ValueError("repo_path unavailable")
    return SQLiteLongTaskStore.for_repo(root), compute_repo_key(root)


def _coerce_step(step: LongTaskStep | dict[str, str]) -> LongTaskStep:
    if isinstance(step, LongTaskStep):
        return step
    return LongTaskStep(
        step_id=step["step_id"],
        title=step["title"],
        action_type=step["action_type"],
        query_hint=step["query_hint"],
        expected_outcome=step.get("expected_outcome", ""),
        acceptance_hint=step.get("acceptance_hint", ""),
    )


def _new_task_id(user_id: str, repo_key: str, goal: str, now: str) -> str:
    digest = sha256(f"{user_id}:{repo_key}:{goal}:{now}".encode("utf-8")).hexdigest()[:6]
    date = datetime.now(tz=UTC).strftime("%Y%m%d")
    return f"task_{date}_{digest}"


def _utc_now() -> str:
    return datetime.now(tz=UTC).isoformat(timespec="microseconds")


def _limit(value: str, max_chars: int) -> str:
    value = value.strip()
    if len(value) <= max_chars:
        return value
    return value[: max_chars - 1].rstrip() + "…"
