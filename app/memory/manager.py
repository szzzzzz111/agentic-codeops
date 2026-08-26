import sqlite3
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

from app.memory.store import (
    InMemorySessionMemoryStore,
    SQLiteMemoryStore,
    compute_repo_key,
)

PREF_KIND = "PREF"
LTM_KIND = "LTM"
STM_KIND = "STM"
MEMORY_UNAVAILABLE_ANSWER = "无法写入记忆：当前仓库记忆存储不可用。"
_REMEMBER_PREFIXES = ("记住:", "请记住", "remember:")
_FORGET_PREFIXES = ("忘记:", "请忘记", "forget:")
_PREF_PREFIXES = ("pref:", "偏好:")
_PROJECT_PREFIXES = ("project:", "项目:")
_STM_PREFIXES = ("stm:", "会话:")
_PREF_HINTS = ("默认", "喜欢", "以后")


@dataclass(frozen=True)
class MemoryCommandResult:
    handled: bool
    answer: str = ""
    audit_summary: str = ""


class MemoryManager:
    def __init__(
        self,
        *,
        session_store: InMemorySessionMemoryStore | None = None,
    ) -> None:
        self.session_store = session_store or InMemorySessionMemoryStore()

    def handle_command(
        self,
        *,
        user_id: str,
        session_id: str,
        repo_path: str | Path,
        message: str,
    ) -> MemoryCommandResult:
        normalized = _normalize_message(message)
        if _matches_prefix(normalized, _REMEMBER_PREFIXES):
            return self.remember(
                user_id=user_id,
                session_id=session_id,
                repo_path=repo_path,
                message=message,
            )
        if _matches_prefix(normalized, _FORGET_PREFIXES):
            return self.forget(
                user_id=user_id,
                session_id=session_id,
                repo_path=repo_path,
                message=message,
            )
        return MemoryCommandResult(handled=False)

    def remember(
        self,
        *,
        user_id: str,
        session_id: str,
        repo_path: str | Path,
        message: str,
    ) -> MemoryCommandResult:
        try:
            store, repo_key = _store_for_existing_repo(repo_path)
            parsed = _parse_remember(message)
            if parsed is None:
                return MemoryCommandResult(handled=False)
            kind, key, value = parsed
            if kind == STM_KIND:
                write = self.session_store.upsert(
                    user_id=user_id,
                    session_id=session_id,
                    key=key,
                    value=value,
                )
            else:
                write = store.upsert(
                    kind=kind,
                    user_id=user_id,
                    repo_key=repo_key if kind == LTM_KIND else None,
                    session_id=None,
                    key=key,
                    value=value,
                )
        except (OSError, sqlite3.Error, ValueError):
            return MemoryCommandResult(
                handled=True,
                answer=MEMORY_UNAVAILABLE_ANSWER,
                audit_summary="memory_status=unavailable",
            )

        label = _label_for_kind(kind)
        return MemoryCommandResult(
            handled=True,
            answer=f"已记住{label}：{write.key}。",
            audit_summary=(
                f"memory_status=success; action=remember; kind={kind}; "
                f"replaced={str(write.replaced).lower()}; repo_key_present=true"
            ),
        )

    def forget(
        self,
        *,
        user_id: str,
        session_id: str,
        repo_path: str | Path,
        message: str,
    ) -> MemoryCommandResult:
        try:
            store, repo_key = _store_for_existing_repo(repo_path)
            query = _parse_forget(message)
            if query is None:
                return MemoryCommandResult(handled=False)
            deleted = 0
            for kind, scoped_repo_key in (
                (PREF_KIND, None),
                (LTM_KIND, repo_key),
            ):
                deleted += store.delete(
                    kind=kind,
                    user_id=user_id,
                    repo_key=scoped_repo_key,
                    session_id=None,
                    query=query,
                )
        except (OSError, sqlite3.Error, ValueError):
            return MemoryCommandResult(
                handled=True,
                answer="无法删除记忆：当前仓库记忆存储不可用。",
                audit_summary="memory_status=unavailable",
            )

        return MemoryCommandResult(
            handled=True,
            answer=f"已删除 {deleted} 条记忆。",
            audit_summary=(
                "memory_status=success; action=forget; "
                f"deleted_count={deleted}; repo_key_present=true"
            ),
        )

    def summarize_for_request(
        self,
        *,
        user_id: str,
        session_id: str,
        repo_path: str | Path,
    ) -> str:
        try:
            store, repo_key = _store_for_existing_repo(repo_path)
            pref_count = len(
                store.list(
                    kind=PREF_KIND,
                    user_id=user_id,
                    repo_key=None,
                    session_id=None,
                )
            )
            ltm_count = len(
                store.list(
                    kind=LTM_KIND,
                    user_id=user_id,
                    repo_key=repo_key,
                    session_id=None,
                )
            )
            stm_count = len(self.session_store.list(user_id=user_id, session_id=session_id))
        except (OSError, sqlite3.Error, ValueError):
            return "memory_status=unavailable"
        return (
            "memory_status=success; "
            f"pref_count={pref_count}; ltm_count={ltm_count}; "
            f"stm_count={stm_count}; repo_key_present=true"
        )

    def control_surface_summary(
        self,
        *,
        user_id: str,
        session_id: str,
        repo_path: str | Path,
    ) -> dict[str, str | int]:
        root = Path(repo_path)
        if not root.exists() or not root.is_dir():
            return _unavailable_control_surface_memory_summary()

        stm_count = len(self.session_store.list(user_id=user_id, session_id=session_id))
        db_path = root / ".repopilot" / "memory.sqlite3"
        if not db_path.exists():
            return {
                "available": "true",
                "pref_count": 0,
                "ltm_count": 0,
                "stm_count": stm_count,
            }

        try:
            repo_key = compute_repo_key(root)
            pref_count = _count_memories_readonly(
                db_path=db_path,
                kind=PREF_KIND,
                user_id=user_id,
                repo_key=None,
            )
            ltm_count = _count_memories_readonly(
                db_path=db_path,
                kind=LTM_KIND,
                user_id=user_id,
                repo_key=repo_key,
            )
        except (OSError, sqlite3.Error, ValueError):
            return _unavailable_control_surface_memory_summary(stm_count=stm_count)

        return {
            "available": "true",
            "pref_count": pref_count,
            "ltm_count": ltm_count,
            "stm_count": stm_count,
        }


def _store_for_existing_repo(repo_path: str | Path) -> tuple[SQLiteMemoryStore, str]:
    root = Path(repo_path)
    if not root.exists() or not root.is_dir():
        raise ValueError("repo_path unavailable")
    repo_key = compute_repo_key(root)
    return SQLiteMemoryStore.for_repo(root), repo_key


def _parse_remember(message: str) -> tuple[str, str, str] | None:
    content = _strip_prefix(message, _REMEMBER_PREFIXES)
    if content is None or not content:
        return None
    kind, content = _extract_kind(content)
    if "=" in content:
        key, value = content.split("=", 1)
        key = key.strip()
        value = value.strip()
    else:
        value = content.strip()
        key = _note_key(value)
    if not key or not value:
        return None
    return kind, key, value


def _parse_forget(message: str) -> str | None:
    content = _strip_prefix(message, _FORGET_PREFIXES)
    if content is None:
        return None
    query = content.strip()
    if not query:
        return None
    return query


def _extract_kind(content: str) -> tuple[str, str]:
    stripped = content.strip()
    lowered = stripped.lower()
    for prefix in _STM_PREFIXES:
        if lowered.startswith(prefix):
            return STM_KIND, stripped[len(prefix) :].strip()
    for prefix in _PREF_PREFIXES:
        if lowered.startswith(prefix):
            return PREF_KIND, stripped[len(prefix) :].strip()
    for prefix in _PROJECT_PREFIXES:
        if lowered.startswith(prefix):
            return LTM_KIND, stripped[len(prefix) :].strip()
    if any(hint in stripped for hint in _PREF_HINTS):
        return PREF_KIND, stripped
    return LTM_KIND, stripped


def _strip_prefix(message: str, prefixes: tuple[str, ...]) -> str | None:
    normalized = _normalize_message(message)
    lowered = normalized.lower()
    for prefix in prefixes:
        normalized_prefix = _normalize_message(prefix).lower()
        if lowered.startswith(normalized_prefix):
            content = normalized[len(normalized_prefix) :].strip()
            if content.startswith(":"):
                content = content[1:].strip()
            return content
    return None


def _matches_prefix(message: str, prefixes: tuple[str, ...]) -> bool:
    lowered = message.lower()
    return any(lowered.startswith(_normalize_message(prefix).lower()) for prefix in prefixes)


def _normalize_message(message: str) -> str:
    return message.strip().replace("：", ":")


def _note_key(value: str) -> str:
    digest = sha256(value.encode("utf-8")).hexdigest()[:12]
    return f"note_{digest}"


def _label_for_kind(kind: str) -> str:
    if kind == PREF_KIND:
        return "偏好"
    if kind == STM_KIND:
        return "会话记忆"
    return "项目记忆"


def _count_memories_readonly(
    *,
    db_path: Path,
    kind: str,
    user_id: str,
    repo_key: str | None,
) -> int:
    uri = f"file:{db_path.as_posix()}?mode=ro"
    with sqlite3.connect(uri, uri=True) as conn:
        row = conn.execute(
            """
            SELECT COUNT(*)
            FROM memories
            WHERE kind = ?
              AND user_id = ?
              AND COALESCE(repo_key, '') = COALESCE(?, '')
              AND COALESCE(session_id, '') = ''
            """,
            (kind, user_id, repo_key),
        ).fetchone()
    return int(row[0])


def _unavailable_control_surface_memory_summary(
    *,
    stm_count: int = 0,
) -> dict[str, str | int]:
    return {
        "available": "false",
        "pref_count": 0,
        "ltm_count": 0,
        "stm_count": stm_count,
    }
