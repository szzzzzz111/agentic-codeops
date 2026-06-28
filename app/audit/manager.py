from dataclasses import dataclass
from pathlib import PurePosixPath, PureWindowsPath
import re

from app.audit.store import DEFAULT_RECENT_LIMIT, AuditEvent, SQLiteAuditStore


MAX_SUMMARY_CHARS = 500
MAX_PAYLOAD_VALUE_CHARS = 1000
_WINDOWS_ABSOLUTE_PATH_RE = re.compile(
    r"\b[A-Za-z]:[\\/][^\s,;'\")\]]+(?:[\\/][^\s,;'\")\]]+)*"
)
_POSIX_LOCAL_ABSOLUTE_PATH_RE = re.compile(
    r"(?<![\w.])/(?:Users|home|root|tmp|var|etc|opt|mnt|srv)/[^\s,;'\")\]]+"
)
_REPOPILOT_PATH_RE = re.compile(r"\.repopilot[\\/][^\s,;'\")\]]+")
_SECRET_RE = re.compile(
    r"\b[A-Za-z0-9_]*(?:API_KEY|TOKEN|SECRET|PASSWORD)\s*=\s*(?:\"[^\"]*\"|'[^']*'|[^\s,;]+)",
    re.IGNORECASE,
)
_PATCH_ID_RE = re.compile(r"\bpatch_[A-Za-z0-9_]+\b")
_TASK_ID_RE = re.compile(r"\btask_[A-Za-z0-9_]+\b")
_WORKTREE_ID_RE = re.compile(r"\bwt_[A-Za-z0-9_]+\b")
_DANGEROUS_PAYLOAD_KEYS = {
    "diff",
    "diff_text",
    "full_diff",
    "stdout",
    "stderr",
    "evidence_pack",
    "provider_prompt",
    "provider_output",
    "prompt",
    "output",
}


@dataclass(frozen=True)
class AuditRecordInput:
    event_type: str
    status: str
    summary: str
    payload: dict[str, str | int | float | bool]
    related_id: str = ""


class AuditManager:
    def record_events(
        self,
        *,
        repo_path: str,
        user_id: str,
        session_id: str,
        trace_id: str,
        events: list[AuditRecordInput],
    ) -> None:
        if not events:
            return
        store, repo_key = SQLiteAuditStore.for_repo(repo_path)
        for event in events:
            store.insert_event(
                event_type=event.event_type,
                user_id=user_id,
                repo_key=repo_key,
                session_id=session_id,
                trace_id=trace_id,
                related_id=event.related_id,
                status=_safe_scalar(event.status, 80),
                summary=_safe_scalar(event.summary, MAX_SUMMARY_CHARS),
                payload=_safe_payload(event.payload),
            )

    def recent_events(
        self,
        *,
        repo_path: str,
        user_id: str,
        event_type: str | None = None,
        limit: int = DEFAULT_RECENT_LIMIT,
    ) -> list[AuditEvent]:
        existing = SQLiteAuditStore.for_existing_repo(repo_path)
        if existing is None:
            return []
        store, repo_key = existing
        return store.recent_events(
            user_id=user_id,
            repo_key=repo_key,
            limit=limit,
            event_type=event_type,
        )

    def find_events(
        self,
        *,
        repo_path: str,
        user_id: str,
        identifier: str,
        limit: int = DEFAULT_RECENT_LIMIT,
    ) -> list[AuditEvent]:
        existing = SQLiteAuditStore.for_existing_repo(repo_path)
        if existing is None:
            return []
        store, repo_key = existing
        return store.find_by_trace_or_related_id(
            user_id=user_id,
            repo_key=repo_key,
            identifier=identifier,
            limit=limit,
        )


def build_trace_event(
    *,
    status: str,
    route: str,
    tool_count: int,
    trace_event_count: int,
) -> AuditRecordInput:
    return AuditRecordInput(
        event_type="trace",
        status=status,
        summary=f"route={route}; status={status}; tools={tool_count}",
        payload={
            "route": route,
            "status": status,
            "tool_count": tool_count,
            "trace_event_count": trace_event_count,
        },
    )


def build_event_from_trace(
    *,
    event_type: str,
    status: str,
    summary: str,
) -> AuditRecordInput | None:
    related_id = _related_id_from_summary(summary)
    if event_type in {
        "patch_command",
        "patch_proposal_summarized",
        "patch_apply_summarized",
        "patch_verify_apply_summarized",
    }:
        return AuditRecordInput(
            event_type="patch_attempt",
            status=status,
            summary=summary,
            related_id=related_id,
            payload=_parse_summary(summary),
        )
    if event_type == "worktree_disposal_summarized":
        worktree = _WORKTREE_ID_RE.search(summary)
        return AuditRecordInput(
            event_type="worktree_disposal",
            status=status,
            summary=summary,
            related_id="" if worktree is None else worktree.group(0),
            payload=_parse_summary(summary),
        )
    if event_type == "verified_patch_promotion_summarized":
        worktree = _WORKTREE_ID_RE.search(summary)
        return AuditRecordInput(
            event_type="verified_patch_promotion",
            status=status,
            summary=summary,
            related_id="" if worktree is None else worktree.group(0),
            payload=_parse_summary(summary),
        )
    if event_type == "repo_mutation_lock":
        return AuditRecordInput(
            event_type="repo_mutation_lock",
            status=status,
            summary=summary,
            related_id=related_id,
            payload=_parse_summary(summary),
        )
    if event_type in {
        "verification_summarized",
        "patch_verify_verification_summarized",
        "worktree_reverification_summarized",
    }:
        return AuditRecordInput(
            event_type="verification_result",
            status=status,
            summary=summary,
            related_id=related_id
            if event_type == "worktree_reverification_summarized"
            else "",
            payload=_parse_summary(summary),
        )
    if event_type in {
        "worktree_create_summarized",
        "worktree_patch_summarized",
        "worktree_verification_summarized",
        "worktree_status",
    }:
        return AuditRecordInput(
            event_type="worktree_event",
            status=status,
            summary=summary,
            related_id=related_id,
            payload=_parse_summary(summary),
        )
    if event_type == "long_task_command":
        return AuditRecordInput(
            event_type="task_event",
            status=status,
            summary=summary,
            related_id=related_id,
            payload=_parse_summary(summary),
        )
    return None


def format_recovery_answer(events: list[AuditEvent], *, empty_label: str) -> str:
    if not events:
        return f"暂无持久审计记录：{empty_label}。"
    lines = ["最近持久审计记录："]
    for event in events:
        related = f"; related_id={event.related_id}" if event.related_id else ""
        lines.append(
            f"- {event.created_at} {event.event_type}/{event.status} "
            f"{event.event_id}{related}: {event.summary}"
        )
    return "\n".join(lines)


def is_audit_recovery_request(message: str) -> bool:
    lowered = message.lower()
    return any(
        term in lowered or term in message
        for term in (
            "audit",
            "recovery",
            "最近审计",
            "审计记录",
            "恢复状态",
            "最近验证",
            "查看 trace",
            "trace_",
            "查看 patch",
            "patch_",
        )
    )


def recovery_query(message: str) -> tuple[str, str | None]:
    lowered = message.lower()
    trace_match = re.search(r"\btrace_[A-Za-z0-9_]+\b", message)
    if trace_match:
        return "identifier", trace_match.group(0)
    patch_match = _PATCH_ID_RE.search(message)
    if patch_match and ("查看" in message or "audit" in lowered or "recovery" in lowered):
        return "identifier", patch_match.group(0)
    if "最近验证" in message or "verification" in lowered:
        return "verification_result", None
    return "recent", None


def _safe_payload(
    payload: dict[str, str | int | float | bool],
) -> dict[str, str | int | float | bool]:
    safe: dict[str, str | int | float | bool] = {}
    for key, value in payload.items():
        if key in _DANGEROUS_PAYLOAD_KEYS:
            continue
        if isinstance(value, bool | int | float):
            safe[key] = value
        else:
            safe[key] = _safe_scalar(value, MAX_PAYLOAD_VALUE_CHARS)
    return safe


def _safe_scalar(value: object, max_chars: int) -> str:
    text = str(value)
    text = _SECRET_RE.sub("<redacted-secret>", text)
    text = _REPOPILOT_PATH_RE.sub(".repopilot/<redacted>", text)
    text = _WINDOWS_ABSOLUTE_PATH_RE.sub("<local-path>", text)
    text = _POSIX_LOCAL_ABSOLUTE_PATH_RE.sub("<local-path>", text)
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1].rstrip() + "…"


def _parse_summary(summary: str) -> dict[str, str]:
    payload: dict[str, str] = {}
    for part in summary.split(";"):
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        key = key.strip()
        if key:
            payload[key] = value.strip()
    return payload


def _related_id_from_summary(summary: str) -> str:
    patch = _PATCH_ID_RE.search(summary)
    if patch:
        return patch.group(0)
    task = _TASK_ID_RE.search(summary)
    if task:
        return task.group(0)
    worktree = _WORKTREE_ID_RE.search(summary)
    if worktree:
        return worktree.group(0)
    return ""


def is_absolute_path(value: str) -> bool:
    return PureWindowsPath(value).is_absolute() or PurePosixPath(value).is_absolute()
