from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import PurePosixPath
from typing import TYPE_CHECKING, Any

from app.verification.runner import command_argv

if TYPE_CHECKING:
    from app.verification.runner import VerificationRunResult


_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_HEAD_RE = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
_REASON_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")
_REGULAR_MODE_RE = re.compile(r"^10[0-7]{4}$")
_SUCCESS_STATUS = "success"
_VERIFICATION_STATUSES = {"failed", "rejected", "success", "timed_out", "unavailable"}


class ClaimState(str, Enum):
    PENDING = "pending"
    READY_FOR_REVIEW = "ready_for_review"
    FAILED = "failed"
    NOT_OBSERVED = "not_observed"
    INVALID = "invalid"


class DecisionOutcome(str, Enum):
    CONTINUE = "continue"
    INTERVENE = "intervene"
    NEEDS_HUMAN = "needs_human"
    READY_FOR_REVIEW = "ready_for_review"


def canonical_sha256(value: Any) -> str:
    if isinstance(value, bytes):
        payload = value
    else:
        payload = json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _require_text(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value or value != value.strip():
        raise ValueError(f"{field_name} must be non-empty and trimmed")


def _require_sha256(value: str | None, field_name: str) -> None:
    if value is None or not _SHA256_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase SHA-256 digest")


def _validate_path(path: str) -> None:
    if not isinstance(path, str) or not path or "\\" in path:
        raise ValueError("paths must be non-empty POSIX paths")
    if path.startswith("/") or path.endswith("/"):
        raise ValueError("paths must be repository-relative")
    parts = path.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise ValueError("paths must be normalized and cannot traverse")
    if PurePosixPath(path).as_posix() != path:
        raise ValueError("paths must be canonical POSIX paths")


def _validate_paths(paths: tuple[str, ...], field_name: str) -> None:
    if not isinstance(paths, tuple):
        raise TypeError(f"{field_name} must be a tuple")
    for path in paths:
        _validate_path(path)
    if tuple(sorted(set(paths))) != paths:
        raise ValueError(f"{field_name} must be sorted and unique")


def _validate_reason_codes(reason_codes: tuple[str, ...]) -> None:
    if not isinstance(reason_codes, tuple) or not reason_codes:
        raise ValueError("reason_codes must be a non-empty tuple")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must be unique")
    if any(not _REASON_RE.fullmatch(reason) for reason in reason_codes):
        raise ValueError("reason_codes must use stable uppercase identifiers")


@dataclass(frozen=True)
class TrackedWorktreeFile:
    path: str
    mode: str
    content_sha256: str

    def __post_init__(self) -> None:
        _validate_path(self.path)
        if not _REGULAR_MODE_RE.fullmatch(self.mode):
            raise ValueError("tracked worktree mode must describe a regular file")
        _require_sha256(self.content_sha256, "content_sha256")


@dataclass(frozen=True)
class TrackedIndexEntry:
    path: str
    mode: str
    object_id: str

    def __post_init__(self) -> None:
        _validate_path(self.path)
        if not _REGULAR_MODE_RE.fullmatch(self.mode):
            raise ValueError("tracked index mode must describe a regular file")
        if not _HEAD_RE.fullmatch(self.object_id):
            raise ValueError("tracked index object_id must be a Git object id")


@dataclass(frozen=True)
class GitSnapshot:
    repository_id: str
    head: str
    status_sha256: str
    tracked_diff_sha256: str
    tracked_changed_paths: tuple[str, ...]
    all_untracked_paths: tuple[str, ...]
    tracked_index_entries: tuple[TrackedIndexEntry, ...]
    tracked_worktree_files: tuple[TrackedWorktreeFile, ...]
    clean: bool
    stability_samples: int = 2

    def __post_init__(self) -> None:
        _require_sha256(self.repository_id, "repository_id")
        if not _HEAD_RE.fullmatch(self.head):
            raise ValueError("head must be a lowercase Git object id")
        _require_sha256(self.status_sha256, "status_sha256")
        _require_sha256(self.tracked_diff_sha256, "tracked_diff_sha256")
        _validate_paths(self.tracked_changed_paths, "tracked_changed_paths")
        _validate_paths(self.all_untracked_paths, "all_untracked_paths")
        if not isinstance(self.tracked_index_entries, tuple):
            raise TypeError("tracked_index_entries must be a tuple")
        for index_entry in self.tracked_index_entries:
            if not isinstance(index_entry, TrackedIndexEntry):
                raise TypeError("tracked_index_entries entries must be typed")
            index_entry.__post_init__()
        index_paths = tuple(item.path for item in self.tracked_index_entries)
        if tuple(sorted(set(index_paths))) != index_paths:
            raise ValueError("tracked_index_entries must be path-sorted and unique")
        if not isinstance(self.tracked_worktree_files, tuple):
            raise TypeError("tracked_worktree_files must be a tuple")
        for tracked_file in self.tracked_worktree_files:
            if not isinstance(tracked_file, TrackedWorktreeFile):
                raise TypeError("tracked_worktree_files entries must be typed")
            tracked_file.__post_init__()
        raw_paths = tuple(item.path for item in self.tracked_worktree_files)
        if tuple(sorted(set(raw_paths))) != raw_paths:
            raise ValueError("tracked_worktree_files must be path-sorted and unique")
        if set(self.tracked_changed_paths) & set(self.all_untracked_paths):
            raise ValueError("tracked and untracked path inventories cannot overlap")
        if set(index_paths) & set(self.all_untracked_paths):
            raise ValueError("index and untracked path inventories cannot overlap")
        if not isinstance(self.clean, bool):
            raise TypeError("clean must be boolean")
        if self.stability_samples != 2:
            raise ValueError("snapshots require exactly two stable samples")
        empty = canonical_sha256(b"")
        inferred_clean = (
            self.status_sha256 == empty
            and self.tracked_diff_sha256 == empty
            and not self.tracked_changed_paths
            and not self.all_untracked_paths
        )
        if self.clean != inferred_clean:
            raise ValueError("clean flag is inconsistent with snapshot evidence")
        if not self.clean and self.status_sha256 == empty:
            raise ValueError("non-clean snapshots require non-empty status evidence")
        if self.tracked_changed_paths and self.tracked_diff_sha256 == empty:
            raise ValueError("tracked paths require non-empty diff evidence")
        if not self.tracked_changed_paths and self.tracked_diff_sha256 != empty:
            raise ValueError("tracked diff evidence requires tracked paths")


@dataclass(frozen=True)
class RunContract:
    run_id: str
    baseline_repository_id: str
    baseline_head: str
    baseline_snapshot_sha256: str
    allowed_tracked_paths: tuple[str, ...]
    verification_label: str
    verification_argv_sha256: str

    def __post_init__(self) -> None:
        _require_text(self.run_id, "run_id")
        _require_sha256(self.baseline_repository_id, "baseline_repository_id")
        if not _HEAD_RE.fullmatch(self.baseline_head):
            raise ValueError("baseline_head must be a lowercase Git object id")
        _require_sha256(self.baseline_snapshot_sha256, "baseline_snapshot_sha256")
        _validate_paths(self.allowed_tracked_paths, "allowed_tracked_paths")
        if not self.allowed_tracked_paths:
            raise ValueError("allowed_tracked_paths cannot be empty")
        _require_text(self.verification_label, "verification_label")
        _require_sha256(self.verification_argv_sha256, "verification_argv_sha256")
        if current_verification_argv_sha256(self.verification_label) is None:
            raise ValueError("verification_label is not whitelisted")


@dataclass(frozen=True)
class AgentClaim:
    provider: str
    run_id: str
    thread_id: str
    stream_closed: bool
    state: ClaimState
    event_stream_sha256: str
    claim_text: str | None = None
    bound_snapshot_sha256: str | None = None
    reason_codes: tuple[str, ...] = ("NOT_OBSERVED",)

    def __post_init__(self) -> None:
        _require_text(self.provider, "provider")
        _require_text(self.run_id, "run_id")
        _require_text(self.thread_id, "thread_id")
        if not isinstance(self.stream_closed, bool):
            raise TypeError("stream_closed must be boolean")
        if not isinstance(self.state, ClaimState):
            raise TypeError("state must be ClaimState")
        _require_sha256(self.event_stream_sha256, "event_stream_sha256")
        _validate_reason_codes(self.reason_codes)
        if self.state is ClaimState.READY_FOR_REVIEW:
            if not self.stream_closed:
                raise ValueError("ready claim requires a closed stream")
            if self.claim_text != "READY_FOR_REVIEW":
                raise ValueError("ready claim text must be exact")
            _require_sha256(self.bound_snapshot_sha256, "bound_snapshot_sha256")
        elif self.claim_text is not None or self.bound_snapshot_sha256 is not None:
            raise ValueError("only ready claims may carry claim text or snapshot binding")
        if self.state is ClaimState.PENDING and self.stream_closed:
            raise ValueError("pending claim requires an open stream")
        if self.state in {ClaimState.FAILED, ClaimState.NOT_OBSERVED} and not self.stream_closed:
            raise ValueError("terminal claim state requires a closed stream")


@dataclass(frozen=True)
class VerificationReceipt:
    run_id: str
    thread_id: str
    provider: str
    event_stream_sha256: str
    claim_sha256: str
    verification_label: str
    verification_argv_sha256: str
    verification_result_sha256: str
    verification_status: str
    exit_code: int | None
    bound_snapshot_sha256: str
    post_verification_snapshot: GitSnapshot

    def __post_init__(self) -> None:
        _require_text(self.run_id, "run_id")
        _require_text(self.thread_id, "thread_id")
        _require_text(self.provider, "provider")
        _require_sha256(self.event_stream_sha256, "event_stream_sha256")
        _require_sha256(self.claim_sha256, "claim_sha256")
        _require_text(self.verification_label, "verification_label")
        _require_sha256(self.verification_argv_sha256, "verification_argv_sha256")
        _require_sha256(self.verification_result_sha256, "verification_result_sha256")
        _require_text(self.verification_status, "verification_status")
        if self.verification_status not in _VERIFICATION_STATUSES:
            raise ValueError("verification_status is not recognized")
        if self.exit_code is not None and not isinstance(self.exit_code, int):
            raise ValueError("exit_code must be int or None")
        if self.verification_status == _SUCCESS_STATUS and self.exit_code != 0:
            raise ValueError("successful verification requires exit code zero")
        if self.verification_status != _SUCCESS_STATUS and self.exit_code == 0:
            raise ValueError("non-successful verification cannot have exit code zero")
        _require_sha256(self.bound_snapshot_sha256, "bound_snapshot_sha256")
        if not isinstance(self.post_verification_snapshot, GitSnapshot):
            raise TypeError("post_verification_snapshot must be GitSnapshot")

    @property
    def passed(self) -> bool:
        return self.verification_status == _SUCCESS_STATUS and self.exit_code == 0


@dataclass(frozen=True)
class GovernanceDecision:
    outcome: DecisionOutcome
    reason_codes: tuple[str, ...]
    task_complete: bool = False
    product_acceptance: bool = False
    git_delivery_authorized: bool = False
    source_provenance: str = "unverified"
    snapshot_continuity: str = "stable_endpoint_samples_only"

    def __post_init__(self) -> None:
        if not isinstance(self.outcome, DecisionOutcome):
            raise TypeError("outcome must be DecisionOutcome")
        _validate_reason_codes(self.reason_codes)
        if self.task_complete or self.product_acceptance or self.git_delivery_authorized:
            raise ValueError("governance decisions cannot elevate completion or delivery")
        if self.source_provenance != "unverified":
            raise ValueError("source provenance is unverified in this stage")
        if self.snapshot_continuity != "stable_endpoint_samples_only":
            raise ValueError("snapshot continuity exceeds this stage's evidence")


def snapshot_sha256(snapshot: GitSnapshot) -> str:
    if not isinstance(snapshot, GitSnapshot):
        raise TypeError("snapshot must be GitSnapshot")
    snapshot.__post_init__()
    return canonical_sha256(asdict(snapshot))


def claim_sha256(claim: AgentClaim) -> str:
    if not isinstance(claim, AgentClaim):
        raise TypeError("claim must be AgentClaim")
    claim.__post_init__()
    return canonical_sha256(asdict(claim))


def current_verification_argv_sha256(label: str) -> str | None:
    argv = command_argv(label)
    return None if argv is None else canonical_sha256(argv)


def build_run_contract(
    *,
    run_id: str,
    baseline_snapshot: GitSnapshot,
    allowed_tracked_paths: tuple[str, ...],
    verification_label: str,
) -> RunContract:
    baseline_snapshot.__post_init__()
    if not baseline_snapshot.clean:
        raise ValueError("baseline snapshot must be clean")
    argv_sha256 = current_verification_argv_sha256(verification_label)
    if argv_sha256 is None:
        raise ValueError("verification_label is not whitelisted")
    return RunContract(
        run_id=run_id,
        baseline_repository_id=baseline_snapshot.repository_id,
        baseline_head=baseline_snapshot.head,
        baseline_snapshot_sha256=snapshot_sha256(baseline_snapshot),
        allowed_tracked_paths=allowed_tracked_paths,
        verification_label=verification_label,
        verification_argv_sha256=argv_sha256,
    )


def build_verification_receipt(
    *,
    verification_result: VerificationRunResult,
    claim: AgentClaim,
    post_verification_snapshot: GitSnapshot,
) -> VerificationReceipt:
    from app.verification.runner import VerificationRunResult

    if not isinstance(verification_result, VerificationRunResult):
        raise TypeError("verification_result must be VerificationRunResult")
    claim.__post_init__()
    post_verification_snapshot.__post_init__()
    if claim.state is not ClaimState.READY_FOR_REVIEW:
        raise ValueError("verification receipt requires a ready claim")
    if claim.bound_snapshot_sha256 != snapshot_sha256(post_verification_snapshot):
        raise ValueError("post-verification snapshot does not match ready claim")
    argv_sha256 = current_verification_argv_sha256(verification_result.command_label)
    if argv_sha256 is None:
        raise ValueError("verification result command is not whitelisted")
    return VerificationReceipt(
        run_id=claim.run_id,
        thread_id=claim.thread_id,
        provider=claim.provider,
        event_stream_sha256=claim.event_stream_sha256,
        claim_sha256=claim_sha256(claim),
        verification_label=verification_result.command_label,
        verification_argv_sha256=argv_sha256,
        verification_result_sha256=canonical_sha256(
            verification_result.audit_summary()
        ),
        verification_status=verification_result.status,
        exit_code=verification_result.exit_code,
        bound_snapshot_sha256=claim.bound_snapshot_sha256,
        post_verification_snapshot=post_verification_snapshot,
    )
