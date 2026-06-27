from dataclasses import dataclass
import difflib
from pathlib import Path
import re
import sqlite3

from app.patching.apply import _apply_file_patch, _parse_unified_diff, _safe_target
from app.patching.store import (
    PATCH_STATUS_APPLIED_IN_WORKTREE,
    PATCH_STATUS_PROMOTED,
    PendingPatch,
    hash_diff,
)
from app.worktrees.disposal import preflight_worktree_disposal
from app.worktrees.git_metadata import git_metadata_text
from app.worktrees.store import (
    WORKTREE_STATUS_PROMOTED,
    WORKTREE_STATUS_VERIFICATION_SUCCEEDED,
    SQLiteWorktreeStore,
    WorktreeRecord,
)


_COMMAND_RE = re.compile(
    r"^(?:confirm\s+promote\s+worktree|确认提升\s+worktree)\s+"
    r"(wt_[A-Za-z0-9_]+)$",
    re.IGNORECASE,
)
_COMMAND_LIKE_RE = re.compile(
    r"(?:promote\s+worktree|提升\s+worktree)", re.IGNORECASE
)
_WORKTREE_ID_RE = re.compile(r"wt_[A-Za-z0-9_]+")


@dataclass(frozen=True)
class VerifiedPatchPromotionRequest:
    handled: bool
    worktree_id: str = ""
    confirmed: bool = False
    rejected: bool = False
    reason: str = ""


@dataclass(frozen=True)
class VerifiedPatchPromotionPreflight:
    accepted: bool
    reason: str
    repo_root: Path | None = None
    record: WorktreeRecord | None = None
    patch: PendingPatch | None = None
    worktree_store: SQLiteWorktreeStore | None = None
    patch_store: object | None = None
    repo_key: str = ""
    rollback_diff: str = ""


@dataclass(frozen=True)
class VerifiedPatchPromotionCompletion:
    succeeded: bool
    reason: str


def parse_verified_patch_promotion_request(message: str) -> VerifiedPatchPromotionRequest:
    normalized = " ".join(message.strip().split())
    match = _COMMAND_RE.fullmatch(normalized)
    if match is not None:
        return VerifiedPatchPromotionRequest(
            handled=True,
            worktree_id=match.group(1),
            confirmed=True,
        )
    if _COMMAND_LIKE_RE.search(normalized):
        worktree_id = _WORKTREE_ID_RE.search(normalized)
        return VerifiedPatchPromotionRequest(
            handled=True,
            worktree_id="" if worktree_id is None else worktree_id.group(0),
            rejected=True,
            reason="invalid_or_unconfirmed_promotion_command",
        )
    return VerifiedPatchPromotionRequest(handled=False)


def preflight_verified_patch_promotion(
    *, repo_path: str, user_id: str, worktree_id: str
) -> VerifiedPatchPromotionPreflight:
    if not _WORKTREE_ID_RE.fullmatch(worktree_id):
        return VerifiedPatchPromotionPreflight(False, "invalid_request")
    try:
        repo_root = Path(repo_path).resolve(strict=True)
        consistency = preflight_worktree_disposal(
            repo_path=str(repo_root),
            user_id=user_id,
            worktree_id=worktree_id,
            attempt_kind="discard",
        )
        if not consistency.accepted:
            return VerifiedPatchPromotionPreflight(False, consistency.reason)
        record = consistency.record
        patch = consistency.patch_store.get_patch(
            record.patch_id, user_id=user_id, repo_key=consistency.repo_key
        )
        if record is None or patch is None:
            return VerifiedPatchPromotionPreflight(False, "metadata_invalid")
        if record.status == WORKTREE_STATUS_PROMOTED or patch.status == PATCH_STATUS_PROMOTED:
            return VerifiedPatchPromotionPreflight(False, "already_promoted")
        if record.status != WORKTREE_STATUS_VERIFICATION_SUCCEEDED:
            return VerifiedPatchPromotionPreflight(False, "worktree_status_ineligible")
        if patch.status != PATCH_STATUS_APPLIED_IN_WORKTREE:
            return VerifiedPatchPromotionPreflight(False, "patch_state_invalid")
        if consistency.classification != "consistent" or not consistency.locked:
            return VerifiedPatchPromotionPreflight(False, "worktree_consistency_invalid")
        main_status = git_metadata_text(
            repo_root, "status", "--porcelain", "--untracked-files=all"
        )
        if main_status is None:
            return VerifiedPatchPromotionPreflight(False, "main_workspace_unavailable")
        if main_status.strip():
            return VerifiedPatchPromotionPreflight(False, "main_workspace_dirty")
        head = git_metadata_text(repo_root, "rev-parse", "HEAD")
        if head is None or head.strip() != record.base_commit:
            return VerifiedPatchPromotionPreflight(False, "main_head_base_mismatch")
        if hash_diff(patch.diff_text) != patch.diff_hash:
            return VerifiedPatchPromotionPreflight(False, "patch_hash_mismatch")
        promotion_state = consistency.patch_store.promotion_state(
            patch_id=patch.patch_id,
            worktree_id=record.worktree_id,
            user_id=user_id,
            repo_key=consistency.repo_key,
        )
        if promotion_state not in {None, "apply_failed"}:
            return VerifiedPatchPromotionPreflight(False, "promotion_state_unresolved")
        content_matches, rollback_diff = _worktree_matches_stored_patch(
            repo_root=repo_root,
            worktree_path=consistency.expected,
            patch=patch,
        )
        if not content_matches:
            return VerifiedPatchPromotionPreflight(False, "worktree_content_mismatch")
        return VerifiedPatchPromotionPreflight(
            True,
            "ok",
            repo_root=repo_root,
            record=record,
            patch=patch,
            worktree_store=consistency.worktree_store,
            patch_store=consistency.patch_store,
            repo_key=consistency.repo_key,
            rollback_diff=rollback_diff,
        )
    except (OSError, RuntimeError, sqlite3.Error, UnicodeError, ValueError, AttributeError):
        return VerifiedPatchPromotionPreflight(False, "metadata_invalid")


def begin_verified_patch_promotion(
    preflight: VerifiedPatchPromotionPreflight,
) -> bool:
    if not preflight.accepted or preflight.record is None or preflight.patch is None:
        return False
    try:
        return bool(
            preflight.patch_store.begin_promotion(
                patch_id=preflight.patch.patch_id,
                worktree_id=preflight.record.worktree_id,
                user_id=preflight.record.user_id,
                repo_key=preflight.repo_key,
            )
        )
    except (sqlite3.Error, OSError, AttributeError):
        return False


def complete_verified_patch_promotion(
    preflight: VerifiedPatchPromotionPreflight,
) -> VerifiedPatchPromotionCompletion:
    if not preflight.accepted or preflight.record is None or preflight.patch is None:
        return VerifiedPatchPromotionCompletion(False, "invalid_preflight")
    record = preflight.record
    patch = preflight.patch
    try:
        if not preflight.patch_store.update_promotion_state(
            patch_id=patch.patch_id,
            worktree_id=record.worktree_id,
            user_id=record.user_id,
            repo_key=preflight.repo_key,
            state="main_applied",
        ):
            return VerifiedPatchPromotionCompletion(False, "state_tracking_failed")
        if not preflight.patch_store.finalize_promotion(
            patch_id=patch.patch_id,
            worktree_id=record.worktree_id,
            user_id=record.user_id,
            repo_key=preflight.repo_key,
            worktree_db_path=preflight.worktree_store.db_path,
        ):
            _mark_state_failure(preflight)
            return VerifiedPatchPromotionCompletion(False, "state_tracking_failed")
    except (sqlite3.Error, OSError, AttributeError):
        _mark_state_failure(preflight)
        return VerifiedPatchPromotionCompletion(False, "state_update_failed")
    return VerifiedPatchPromotionCompletion(True, "promoted")


def mark_verified_patch_promotion_apply_failed(
    preflight: VerifiedPatchPromotionPreflight,
) -> None:
    if preflight.record is None or preflight.patch is None:
        return
    try:
        preflight.patch_store.mark_promotion_apply_failed(
            patch_id=preflight.patch.patch_id,
            worktree_id=preflight.record.worktree_id,
            user_id=preflight.record.user_id,
            repo_key=preflight.repo_key,
        )
    except (sqlite3.Error, OSError, AttributeError):
        return


def _worktree_matches_stored_patch(
    *, repo_root: Path, worktree_path: Path | None, patch: PendingPatch
) -> tuple[bool, str]:
    if worktree_path is None:
        return False, ""
    file_patches = _parse_unified_diff(patch.diff_text)
    changed_files = [file_patch.file_path for file_patch in file_patches]
    if sorted(changed_files) != sorted(patch.target_files):
        return False, ""
    rollback_lines: list[str] = []
    for file_patch in file_patches:
        source = _safe_target(repo_root, file_patch.file_path)
        original = source.read_text(encoding="utf-8")
        expected = _apply_file_patch(original, file_patch)
        candidate = _safe_target(worktree_path, file_patch.file_path)
        if candidate.read_text(encoding="utf-8") != expected:
            return False, ""
        rollback_lines.extend(
            difflib.unified_diff(
                expected.splitlines(),
                original.splitlines(),
                fromfile=f"a/{file_patch.file_path}",
                tofile=f"b/{file_patch.file_path}",
                lineterm="",
            )
        )
    rollback_diff = "\n".join(rollback_lines) + ("\n" if rollback_lines else "")
    return bool(rollback_diff), rollback_diff


def _mark_state_failure(preflight: VerifiedPatchPromotionPreflight) -> None:
    if preflight.record is None or preflight.patch is None:
        return
    try:
        preflight.patch_store.update_promotion_state(
            patch_id=preflight.patch.patch_id,
            worktree_id=preflight.record.worktree_id,
            user_id=preflight.record.user_id,
            repo_key=preflight.repo_key,
            state="state_update_failed",
        )
    except (sqlite3.Error, OSError, AttributeError):
        return
