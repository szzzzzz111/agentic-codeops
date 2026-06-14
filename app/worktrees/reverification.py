from dataclasses import dataclass
import os
from pathlib import Path, PureWindowsPath
import re
import subprocess

from app.verification.runner import parse_verification_label
from app.worktrees.store import (
    WORKTREE_STATUS_PATCH_APPLIED,
    WORKTREE_STATUS_VERIFICATION_FAILED,
    WORKTREE_STATUS_VERIFICATION_SUCCEEDED,
    WorktreeRecord,
)


_PREFIX_RE = re.compile(
    r"^(?:worktree\s+verify|重新验证\s+worktree)\b",
    re.IGNORECASE,
)
_INTENT_RE = re.compile(
    r"(?:worktree\s+verify|重新验证\s+worktree)\b",
    re.IGNORECASE,
)
_COMMAND_RE = re.compile(
    r"^(?:worktree\s+verify|重新验证\s+worktree)\s+"
    r"(wt_[A-Za-z0-9_]+)\s+(.+)$",
    re.IGNORECASE,
)
_WORKTREE_ID_RE = re.compile(r"wt_[A-Za-z0-9_]+")
_OBJECT_ID_RE = re.compile(r"[0-9a-fA-F]{40,64}")
_MAX_GIT_OUTPUT_BYTES = 256_000
_ELIGIBLE_STATUSES = {
    WORKTREE_STATUS_PATCH_APPLIED,
    WORKTREE_STATUS_VERIFICATION_FAILED,
    WORKTREE_STATUS_VERIFICATION_SUCCEEDED,
}


@dataclass(frozen=True)
class WorktreeReverificationRequest:
    handled: bool
    worktree_id: str = ""
    command_label: str = ""
    rejected: bool = False
    reason: str = ""


@dataclass(frozen=True)
class WorktreeReverificationPreflight:
    accepted: bool
    reason: str
    record: WorktreeRecord | None = None
    execution_repo_path: str = ""


def parse_worktree_reverification_request(message: str) -> WorktreeReverificationRequest:
    normalized = " ".join(message.strip().split())
    if not _PREFIX_RE.match(normalized):
        if _INTENT_RE.search(normalized):
            return WorktreeReverificationRequest(
                handled=True,
                worktree_id=_safe_worktree_id(normalized),
                rejected=True,
                reason="invalid_reverification_command",
            )
        return WorktreeReverificationRequest(handled=False)
    match = _COMMAND_RE.fullmatch(normalized)
    if match is None:
        return WorktreeReverificationRequest(
            handled=True,
            worktree_id=_safe_worktree_id(normalized),
            rejected=True,
            reason="invalid_reverification_command",
        )
    worktree_id, raw_label = match.groups()
    parsed_label = parse_verification_label(raw_label)
    if parsed_label.rejected or not parsed_label.command_label:
        return WorktreeReverificationRequest(
            handled=True,
            worktree_id=worktree_id,
            rejected=True,
            reason=parsed_label.reason or "invalid_verification_label",
        )
    return WorktreeReverificationRequest(
        handled=True,
        worktree_id=worktree_id,
        command_label=parsed_label.command_label,
    )


def preflight_worktree_reverification(
    *,
    repo_root: Path,
    record: WorktreeRecord,
) -> WorktreeReverificationPreflight:
    if not _WORKTREE_ID_RE.fullmatch(record.worktree_id) or not _OBJECT_ID_RE.fullmatch(
        record.base_commit
    ):
        return _rejected("metadata_invalid", record)
    if record.status not in _ELIGIBLE_STATUSES:
        return _rejected("worktree_status_ineligible", record)
    managed_root = (repo_root / ".repopilot" / "worktrees").resolve()
    expected = (managed_root / record.worktree_id).resolve()
    if not _is_within(expected, managed_root):
        return _rejected("metadata_invalid", record)
    if not expected.is_dir():
        return _rejected("directory_missing", record)

    registry = _registry_paths(repo_root)
    if registry is None:
        return _rejected("git_registry_unavailable", record)
    normalized_expected = _normalized_path(expected)
    if normalized_expected not in registry:
        return _rejected("git_registry_missing_or_mismatch", record)

    head = _bounded_git_text(expected, "rev-parse", "HEAD")
    if head is None:
        return _rejected("head_unavailable", record)
    if head.strip() != record.base_commit:
        return _rejected("head_base_mismatch", record)
    return WorktreeReverificationPreflight(
        accepted=True,
        reason="ok",
        record=record,
        execution_repo_path=str(expected),
    )


def _registry_paths(repo_root: Path) -> set[str] | None:
    text = _bounded_git_text(repo_root, "worktree", "list", "--porcelain", "-z")
    if text is None:
        return None
    paths: set[str] = set()
    for token in text.split("\0"):
        for line in token.splitlines():
            if line.startswith("worktree "):
                paths.add(_normalized_path(Path(line[9:])))
    return paths


def _bounded_git_text(cwd: Path, *args: str) -> str | None:
    env = os.environ.copy()
    env["GIT_OPTIONAL_LOCKS"] = "0"
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=cwd,
            env=env,
            capture_output=True,
            text=False,
            shell=False,
            check=False,
        )
    except OSError:
        return None
    if result.returncode != 0 or len(result.stdout) > _MAX_GIT_OUTPUT_BYTES:
        return None
    return result.stdout.decode("utf-8", errors="replace")


def _rejected(
    reason: str,
    record: WorktreeRecord | None = None,
) -> WorktreeReverificationPreflight:
    return WorktreeReverificationPreflight(accepted=False, reason=reason, record=record)


def _normalized_path(path: Path) -> str:
    normalized = path.resolve().as_posix()
    return normalized.lower() if PureWindowsPath(normalized).drive else normalized


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _safe_worktree_id(value: str) -> str:
    match = _WORKTREE_ID_RE.search(value)
    return "" if match is None else match.group(0)
