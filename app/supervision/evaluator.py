from __future__ import annotations

from . import contracts as contract_module
from .contracts import (
    AgentClaim,
    ClaimState,
    DecisionOutcome,
    GitSnapshot,
    GovernanceDecision,
    RunContract,
    VerificationReceipt,
    claim_sha256,
    snapshot_sha256,
)


def _decision(outcome: DecisionOutcome, reason: str) -> GovernanceDecision:
    return GovernanceDecision(outcome=outcome, reason_codes=(reason,))


def _raw_changed_paths(
    baseline_snapshot: GitSnapshot,
    current_snapshot: GitSnapshot,
) -> set[str]:
    baseline = {item.path: item for item in baseline_snapshot.tracked_worktree_files}
    current = {item.path: item for item in current_snapshot.tracked_worktree_files}
    return {
        path
        for path in baseline.keys() | current.keys()
        if baseline.get(path) != current.get(path)
    }


def _index_changed_paths(
    baseline_snapshot: GitSnapshot,
    current_snapshot: GitSnapshot,
) -> set[str]:
    baseline = {item.path: item for item in baseline_snapshot.tracked_index_entries}
    current = {item.path: item for item in current_snapshot.tracked_index_entries}
    return {
        path
        for path in baseline.keys() | current.keys()
        if baseline.get(path) != current.get(path)
    }


def evaluate_governed_run(
    contract: RunContract,
    baseline_snapshot: GitSnapshot,
    current_snapshot: GitSnapshot,
    claim: AgentClaim,
    receipt: VerificationReceipt | None = None,
) -> GovernanceDecision:
    try:
        contract.__post_init__()
        baseline_snapshot.__post_init__()
        current_snapshot.__post_init__()
        claim.__post_init__()
        if receipt is not None:
            receipt.__post_init__()
    except (AttributeError, TypeError, ValueError):
        return _decision(DecisionOutcome.INTERVENE, "INVALID_SUPERVISION_INPUT")

    if (
        not baseline_snapshot.clean
        or contract.baseline_snapshot_sha256 != snapshot_sha256(baseline_snapshot)
    ):
        return _decision(DecisionOutcome.INTERVENE, "BASELINE_SNAPSHOT_MISMATCH")
    if (
        baseline_snapshot.repository_id != contract.baseline_repository_id
        or current_snapshot.repository_id != contract.baseline_repository_id
    ):
        return _decision(DecisionOutcome.INTERVENE, "REPOSITORY_MISMATCH")
    if (
        baseline_snapshot.head != contract.baseline_head
        or current_snapshot.head != contract.baseline_head
    ):
        return _decision(DecisionOutcome.INTERVENE, "HEAD_MISMATCH")
    if current_snapshot.all_untracked_paths:
        return _decision(DecisionOutcome.INTERVENE, "UNTRACKED_PATHS_NOT_ALLOWED")
    evidenced_changed_paths = set(current_snapshot.tracked_changed_paths)
    evidenced_changed_paths.update(
        _raw_changed_paths(baseline_snapshot, current_snapshot)
    )
    evidenced_changed_paths.update(
        _index_changed_paths(baseline_snapshot, current_snapshot)
    )
    if not evidenced_changed_paths.issubset(contract.allowed_tracked_paths):
        return _decision(DecisionOutcome.INTERVENE, "OUT_OF_SCOPE_TRACKED_PATH")
    if claim.state is ClaimState.INVALID:
        return _decision(DecisionOutcome.INTERVENE, "INVALID_AGENT_CLAIM")
    if claim.run_id != contract.run_id:
        return _decision(DecisionOutcome.INTERVENE, "CLAIM_CORRELATION_MISMATCH")
    if claim.state is ClaimState.READY_FOR_REVIEW:
        if not evidenced_changed_paths:
            return _decision(DecisionOutcome.INTERVENE, "NO_EVIDENCED_CHANGE")
        if claim.bound_snapshot_sha256 != snapshot_sha256(current_snapshot):
            return _decision(DecisionOutcome.INTERVENE, "CLAIM_SNAPSHOT_MISMATCH")
    argv_sha256 = contract_module.current_verification_argv_sha256(
        contract.verification_label
    )
    if argv_sha256 != contract.verification_argv_sha256:
        return _decision(DecisionOutcome.INTERVENE, "VERIFICATION_COMMAND_MISMATCH")
    if receipt is not None:
        if (
            receipt.run_id != contract.run_id
            or receipt.thread_id != claim.thread_id
            or receipt.provider != claim.provider
            or receipt.event_stream_sha256 != claim.event_stream_sha256
            or receipt.claim_sha256 != claim_sha256(claim)
        ):
            return _decision(
                DecisionOutcome.INTERVENE, "RECEIPT_CORRELATION_MISMATCH"
            )
        if (
            receipt.verification_label != contract.verification_label
            or receipt.verification_argv_sha256 != contract.verification_argv_sha256
        ):
            return _decision(DecisionOutcome.INTERVENE, "VERIFICATION_COMMAND_MISMATCH")
        current_sha256 = snapshot_sha256(current_snapshot)
        if (
            receipt.bound_snapshot_sha256 != current_sha256
            or snapshot_sha256(receipt.post_verification_snapshot) != current_sha256
        ):
            return _decision(DecisionOutcome.INTERVENE, "RECEIPT_SNAPSHOT_MISMATCH")
        if claim.state is not ClaimState.READY_FOR_REVIEW:
            return _decision(
                DecisionOutcome.INTERVENE, "PREMATURE_VERIFICATION_RECEIPT"
            )
    if claim.state is ClaimState.PENDING:
        return _decision(DecisionOutcome.CONTINUE, "AGENT_STREAM_PENDING")
    if claim.state in {ClaimState.FAILED, ClaimState.NOT_OBSERVED}:
        return _decision(DecisionOutcome.NEEDS_HUMAN, "AGENT_EVIDENCE_INCOMPLETE")
    if receipt is None:
        return _decision(DecisionOutcome.NEEDS_HUMAN, "VERIFICATION_RECEIPT_MISSING")

    if not receipt.passed:
        return _decision(DecisionOutcome.NEEDS_HUMAN, "VERIFICATION_NOT_PASSED")
    return _decision(DecisionOutcome.READY_FOR_REVIEW, "VERIFICATION_PASSED")
