from dataclasses import dataclass
import os
from pathlib import Path
import re
import shutil
import sqlite3
import subprocess

from app.patching.store import (
    PATCH_STATUS_APPLIED_IN_WORKTREE,
    PATCH_STATUS_DISCARDED,
    SQLitePatchStore,
)
from app.worktrees.git_metadata import git_metadata_text, normalized_path, registry_entries
from app.worktrees.store import (
    WORKTREE_STATUS_DISCARDED,
    WORKTREE_STATUS_DISPOSAL_FAILED,
    WORKTREE_STATUS_PATCH_APPLIED,
    WORKTREE_STATUS_VERIFICATION_FAILED,
    WORKTREE_STATUS_VERIFICATION_SUCCEEDED,
    SQLiteWorktreeStore,
    WorktreeRecord,
)


_COMMAND_RE = re.compile(
    r"^(?:(confirm)\s+(discard|reconcile)\s+worktree|"
    r"(确认)(丢弃|协调)\s+worktree)\s+(wt_[A-Za-z0-9_]+)$",
    re.IGNORECASE,
)
_COMMAND_LIKE_RE = re.compile(
    r"^(?:(?:confirm\s+)?(?:discard|reconcile)\s+worktree|"
    r"(?:确认)?(?:丢弃|协调)\s+worktree)\b",
    re.IGNORECASE,
)
_WORKTREE_ID_RE = re.compile(r"wt_[A-Za-z0-9_]+")
_OBJECT_ID_RE = re.compile(r"[0-9a-fA-F]{40,64}")
_ELIGIBLE = {
    WORKTREE_STATUS_PATCH_APPLIED,
    WORKTREE_STATUS_VERIFICATION_FAILED,
    WORKTREE_STATUS_VERIFICATION_SUCCEEDED,
}


@dataclass(frozen=True)
class WorktreeDisposalRequest:
    handled: bool
    worktree_id: str = ""
    attempt_kind: str = ""
    confirmed: bool = False
    rejected: bool = False
    reason: str = ""


@dataclass(frozen=True)
class WorktreeDisposalResult:
    succeeded: bool
    reason: str
    attempt_kind: str
    worktree_id: str
    preflight_classification: str = ""
    completed_step: str = ""
    failed_step: str = ""
    mutation_attempted: bool = False
    idempotent: bool = False
    worktree_status: str = ""
    patch_status: str = ""

    @property
    def public_summary(self) -> str:
        status = "succeeded" if self.succeeded else "failed"
        return (
            f"worktree disposal {status}: worktree_id={self.worktree_id}; "
            f"kind={self.attempt_kind}; reason={self.reason}; "
            f"completed_step={self.completed_step or 'none'}"
        )


@dataclass(frozen=True)
class WorktreeDisposalPreflight:
    accepted: bool
    reason: str
    classification: str = ""
    repo_root: Path | None = None
    expected: Path | None = None
    record: WorktreeRecord | None = None
    worktree_store: SQLiteWorktreeStore | None = None
    patch_store: SQLitePatchStore | None = None
    repo_key: str = ""
    registry_present: bool = False
    locked: bool = False
    directory_present: bool = False
    patch_status: str = ""
    idempotent: bool = False
    patch_only: bool = False


def parse_worktree_disposal_request(message: str) -> WorktreeDisposalRequest:
    normalized = " ".join(message.strip().split())
    match = _COMMAND_RE.fullmatch(normalized)
    if match:
        english_kind = match.group(2)
        chinese_kind = match.group(4)
        kind = english_kind or ("discard" if chinese_kind == "丢弃" else "reconcile")
        return WorktreeDisposalRequest(
            handled=True,
            worktree_id=match.group(5),
            attempt_kind=kind.lower(),
            confirmed=True,
        )
    if _COMMAND_LIKE_RE.match(normalized):
        worktree_id = _WORKTREE_ID_RE.search(normalized)
        return WorktreeDisposalRequest(
            handled=True,
            worktree_id="" if worktree_id is None else worktree_id.group(0),
            rejected=True,
            reason="invalid_or_unconfirmed_disposal_command",
        )
    return WorktreeDisposalRequest(handled=False)


def dispose_worktree(
    *,
    repo_path: str,
    user_id: str,
    worktree_id: str,
    attempt_kind: str,
) -> WorktreeDisposalResult:
    preflight = _preflight(
        repo_path=repo_path,
        user_id=user_id,
        worktree_id=worktree_id,
        attempt_kind=attempt_kind,
    )
    if not preflight.accepted:
        return _result(preflight, attempt_kind, worktree_id, reason=preflight.reason)
    assert preflight.record and preflight.worktree_store and preflight.patch_store
    if preflight.idempotent:
        return _result(
            preflight,
            attempt_kind,
            worktree_id,
            succeeded=True,
            reason="already_discarded",
            completed_step="already_discarded",
            idempotent=True,
        )
    if preflight.patch_only:
        updated = preflight.patch_store.mark_status_scoped(
            preflight.record.patch_id,
            user_id=user_id,
            repo_key=preflight.repo_key,
            status=PATCH_STATUS_DISCARDED,
        )
        return _result(
            preflight,
            attempt_kind,
            worktree_id,
            succeeded=updated,
            reason="ok" if updated else "patch_update_failed",
            completed_step="patch_discarded" if updated else "",
            failed_step="" if updated else "patch_update",
        )

    mutation_attempted = False
    completed_step = ""
    attempted_step = ""
    try:
        if preflight.registry_present:
            if preflight.locked:
                mutation_attempted = True
                attempted_step = "unlock"
                _run_mutation(preflight.repo_root, "worktree", "unlock", str(preflight.expected))
                completed_step = "unlock"
            mutation_attempted = True
            attempted_step = "remove"
            _run_mutation(
                preflight.repo_root,
                "worktree",
                "remove",
                "--force",
                str(preflight.expected),
            )
            completed_step = "remove"
        elif preflight.directory_present:
            mutation_attempted = True
            attempted_step = "delete"
            shutil.rmtree(preflight.expected)
            completed_step = "delete"
        attempted_step = "postcheck"
        entries = registry_entries(preflight.repo_root)
        if entries is None or preflight.expected.exists() or normalized_path(preflight.expected) in entries:
            raise RuntimeError("postcheck_failed")
        completed_step = "cleanup_confirmed"
    except (OSError, RuntimeError, subprocess.SubprocessError):
        if mutation_attempted:
            try:
                preflight.worktree_store.update_worktree(
                    worktree_id,
                    user_id=user_id,
                    repo_key=preflight.repo_key,
                    status=WORKTREE_STATUS_DISPOSAL_FAILED,
                )
            except Exception:
                pass
        return _result(
            preflight,
            attempt_kind,
            worktree_id,
            reason="mutation_failed",
            completed_step=completed_step,
            failed_step=attempted_step or "cleanup",
            mutation_attempted=mutation_attempted,
            worktree_status=WORKTREE_STATUS_DISPOSAL_FAILED if mutation_attempted else preflight.record.status,
        )

    try:
        worktree_updated = preflight.worktree_store.update_worktree(
            worktree_id,
            user_id=user_id,
            repo_key=preflight.repo_key,
            status=WORKTREE_STATUS_DISCARDED,
        )
    except Exception:
        worktree_updated = False
    if not worktree_updated:
        return _result(
            preflight,
            attempt_kind,
            worktree_id,
            reason="worktree_update_failed",
            completed_step="cleanup_confirmed",
            failed_step="worktree_update",
            mutation_attempted=mutation_attempted,
        )
    try:
        patch_updated = preflight.patch_store.mark_status_scoped(
            preflight.record.patch_id,
            user_id=user_id,
            repo_key=preflight.repo_key,
            status=PATCH_STATUS_DISCARDED,
        )
    except Exception:
        patch_updated = False
    if not patch_updated:
        return _result(
            preflight,
            attempt_kind,
            worktree_id,
            reason="patch_update_failed",
            completed_step="worktree_discarded",
            failed_step="patch_update",
            mutation_attempted=mutation_attempted,
            worktree_status=WORKTREE_STATUS_DISCARDED,
        )
    return _result(
        preflight,
        attempt_kind,
        worktree_id,
        succeeded=True,
        reason="ok",
        completed_step="patch_discarded",
        mutation_attempted=mutation_attempted,
        worktree_status=WORKTREE_STATUS_DISCARDED,
        patch_status=PATCH_STATUS_DISCARDED,
    )


def preflight_worktree_disposal(
    *,
    repo_path: str,
    user_id: str,
    worktree_id: str,
    attempt_kind: str,
) -> WorktreeDisposalPreflight:
    return _preflight(
        repo_path=repo_path,
        user_id=user_id,
        worktree_id=worktree_id,
        attempt_kind=attempt_kind,
    )


def _preflight(
    *,
    repo_path: str,
    user_id: str,
    worktree_id: str,
    attempt_kind: str,
) -> WorktreeDisposalPreflight:
    if attempt_kind not in {"discard", "reconcile"} or not _WORKTREE_ID_RE.fullmatch(worktree_id):
        return WorktreeDisposalPreflight(False, "invalid_request")
    try:
        repo_root = Path(repo_path).resolve(strict=True)
        existing = SQLiteWorktreeStore.for_existing_repo(repo_root)
        patches = SQLitePatchStore.for_existing_repo(repo_root)
        if existing is None or patches is None:
            return WorktreeDisposalPreflight(False, "worktree_not_found")
        worktree_store, repo_key = existing
        patch_store, patch_repo_key = patches
        if repo_key != patch_repo_key:
            return WorktreeDisposalPreflight(False, "scope_invalid")
        record = worktree_store.get_worktree(worktree_id, user_id=user_id, repo_key=repo_key)
        if record is None:
            return WorktreeDisposalPreflight(False, "worktree_not_found")
        patch = patch_store.get_patch(record.patch_id, user_id=user_id, repo_key=repo_key)
        if patch is None or patch.status not in {
            PATCH_STATUS_APPLIED_IN_WORKTREE,
            PATCH_STATUS_DISCARDED,
        }:
            return WorktreeDisposalPreflight(False, "patch_state_invalid", record=record)
        if record.status == WORKTREE_STATUS_DISCARDED:
            if patch.status != PATCH_STATUS_DISCARDED and attempt_kind != "reconcile":
                return WorktreeDisposalPreflight(
                    False,
                    "reconciliation_required",
                    record=record,
                )
            return WorktreeDisposalPreflight(
                True,
                "ok",
                "terminal",
                repo_root,
                record=record,
                worktree_store=worktree_store,
                patch_store=patch_store,
                repo_key=repo_key,
                patch_status=patch.status,
                idempotent=patch.status == PATCH_STATUS_DISCARDED,
                patch_only=patch.status != PATCH_STATUS_DISCARDED and attempt_kind == "reconcile",
            )
        if record.status not in _ELIGIBLE | {WORKTREE_STATUS_DISPOSAL_FAILED}:
            return WorktreeDisposalPreflight(False, "worktree_status_ineligible", record=record)
        if patch.status != PATCH_STATUS_APPLIED_IN_WORKTREE:
            return WorktreeDisposalPreflight(False, "patch_state_invalid", record=record)
        if attempt_kind == "discard" and record.status == WORKTREE_STATUS_DISPOSAL_FAILED:
            return WorktreeDisposalPreflight(False, "reconciliation_required", record=record)
        if not _OBJECT_ID_RE.fullmatch(record.base_commit):
            return WorktreeDisposalPreflight(False, "metadata_invalid", record=record)
        managed_root = repo_root / ".repopilot" / "worktrees"
        expected = managed_root / worktree_id
        if expected == repo_root or expected == managed_root or not _is_within(expected, managed_root):
            return WorktreeDisposalPreflight(False, "unsafe_path", record=record)
        directory_present = expected.exists()
        if directory_present and (_is_reparse(expected) or not expected.is_dir()):
            return WorktreeDisposalPreflight(False, "unsafe_path", record=record)
        entries = registry_entries(repo_root)
        if entries is None:
            return WorktreeDisposalPreflight(False, "git_registry_unavailable", record=record)
        entry = entries.get(normalized_path(expected))
        registry_present = entry is not None
        if not registry_present and _registry_path_mismatch(
            repo_root,
            expected,
            worktree_id,
            entries,
        ):
            return WorktreeDisposalPreflight(False, "registry_path_mismatch", record=record)
        if attempt_kind == "discard" and not (directory_present and registry_present):
            return WorktreeDisposalPreflight(False, "consistency_mismatch", record=record)
        if directory_present and not _ownership_matches(repo_root, expected, record.base_commit):
            return WorktreeDisposalPreflight(False, "ownership_or_head_mismatch", record=record)
        classification = (
            "consistent"
            if directory_present and registry_present
            else "directory_missing"
            if registry_present
            else "registry_missing"
            if directory_present
            else "both_missing"
        )
        return WorktreeDisposalPreflight(
            True,
            "ok",
            classification,
            repo_root,
            expected,
            record,
            worktree_store,
            patch_store,
            repo_key,
            registry_present,
            bool(entry and entry.locked),
            directory_present,
            patch.status,
        )
    except (OSError, RuntimeError, sqlite3.Error, UnicodeError, ValueError):
        return WorktreeDisposalPreflight(False, "metadata_invalid")


def _registry_path_mismatch(
    repo_root: Path,
    expected: Path,
    worktree_id: str,
    entries: dict[str, object],
) -> bool:
    common = git_metadata_text(repo_root, "rev-parse", "--git-common-dir")
    if common is None:
        raise RuntimeError("git_common_dir_unavailable")
    common_path = (repo_root / common.strip()).resolve()
    admin_root = common_path / "worktrees"
    admin = admin_root / worktree_id
    if not admin.exists():
        return False
    if not admin.is_dir() or admin.is_symlink() or not _is_within(admin, admin_root):
        raise RuntimeError("worktree_admin_invalid")
    backref = admin / "gitdir"
    if not backref.is_file() or backref.is_symlink():
        raise RuntimeError("worktree_admin_backref_invalid")
    target = Path(backref.read_text(encoding="utf-8", errors="strict").strip())
    if not target.is_absolute():
        target = (admin / target).resolve()
    registered = target.resolve().parent
    registered_key = normalized_path(registered)
    if registered_key == normalized_path(expected):
        raise RuntimeError("expected_registry_entry_missing")
    if registered_key not in entries:
        raise RuntimeError("worktree_registry_backref_mismatch")
    return True


def _ownership_matches(repo_root: Path, expected: Path, base_commit: str) -> bool:
    git_file = expected / ".git"
    if not git_file.is_file() or git_file.is_symlink():
        return False
    inside = git_metadata_text(expected, "rev-parse", "--is-inside-work-tree")
    top = git_metadata_text(expected, "rev-parse", "--show-toplevel")
    common = git_metadata_text(expected, "rev-parse", "--git-common-dir")
    head = git_metadata_text(expected, "rev-parse", "HEAD")
    if None in {inside, top, common, head}:
        return False
    repo_common = git_metadata_text(repo_root, "rev-parse", "--git-common-dir")
    if repo_common is None:
        return False
    common_path = (expected / common.strip()).resolve()
    repo_common_path = (repo_root / repo_common.strip()).resolve()
    if inside.strip() != "true" or normalized_path(Path(top.strip())) != normalized_path(expected):
        return False
    if normalized_path(common_path) != normalized_path(repo_common_path):
        return False
    if head.strip() != base_commit:
        return False
    first = git_file.read_text(encoding="utf-8", errors="strict").strip()
    if not first.startswith("gitdir: "):
        return False
    admin = Path(first[8:])
    if not admin.is_absolute():
        admin = (expected / admin).resolve()
    admin_root = common_path / "worktrees"
    if not _is_within(admin.resolve(), admin_root.resolve()):
        return False
    backref = admin / "gitdir"
    if not backref.is_file() or backref.is_symlink():
        return False
    target = Path(backref.read_text(encoding="utf-8", errors="strict").strip())
    if not target.is_absolute():
        target = (admin / target).resolve()
    return normalized_path(target) == normalized_path(git_file)


def _run_mutation(cwd: Path, *args: str) -> None:
    env = os.environ.copy()
    env["GIT_OPTIONAL_LOCKS"] = "0"
    subprocess.run(
        ["git", *args],
        cwd=cwd,
        env=env,
        check=True,
        capture_output=True,
        timeout=20,
        shell=False,
    )


def _is_reparse(path: Path) -> bool:
    if path.is_symlink():
        return True
    attributes = getattr(path.stat(), "st_file_attributes", 0)
    return bool(attributes & getattr(os, "FILE_ATTRIBUTE_REPARSE_POINT", 0))


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
    except ValueError:
        return False
    return True


def _result(
    preflight: WorktreeDisposalPreflight,
    attempt_kind: str,
    worktree_id: str,
    *,
    succeeded: bool = False,
    reason: str,
    completed_step: str = "",
    failed_step: str = "",
    mutation_attempted: bool = False,
    idempotent: bool = False,
    worktree_status: str = "",
    patch_status: str = "",
) -> WorktreeDisposalResult:
    return WorktreeDisposalResult(
        succeeded=succeeded,
        reason=reason,
        attempt_kind=attempt_kind,
        worktree_id=worktree_id,
        preflight_classification=preflight.classification,
        completed_step=completed_step,
        failed_step=failed_step,
        mutation_attempted=mutation_attempted,
        idempotent=idempotent,
        worktree_status=worktree_status or (preflight.record.status if preflight.record else ""),
        patch_status=patch_status or preflight.patch_status,
    )
