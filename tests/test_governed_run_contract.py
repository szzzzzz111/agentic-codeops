from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import pytest

import app.supervision.git_snapshot as snapshot_module
from app.supervision import (
    AgentClaim,
    ClaimState,
    DecisionOutcome,
    GitSnapshot,
    GovernanceDecision,
    RunContract,
    TrackedIndexEntry,
    TrackedWorktreeFile,
    VerificationReceipt,
    adapt_codex_events,
    build_run_contract,
    build_verification_receipt,
    canonical_sha256,
    claim_sha256,
    collect_git_snapshot,
    evaluate_governed_run,
    snapshot_sha256,
)
from app.supervision.git_snapshot import (
    GitSnapshotCollectionError,
    _controlled_git_env,
    _run_bounded_process,
)
from app.verification.runner import VerificationRunResult

EMPTY_SHA256 = canonical_sha256(b"")
HEAD = "1" * 40
REPOSITORY_ID = "2" * 64
ARCHIVED_OBSERVATION = Path(
    "openspec/changes/archive/2026-09-01-qualify-real-agent-observability/"
    "qualification-observation.json"
)
POSIX_ONLY = pytest.mark.skipif(
    not snapshot_module._process_isolation_supported(),
    reason="the current collector fails closed without POSIX process-group isolation",
)


def _snapshot(
    *,
    changed: tuple[str, ...] = (),
    untracked: tuple[str, ...] = (),
    head: str = HEAD,
    repository_id: str = REPOSITORY_ID,
) -> GitSnapshot:
    clean = not changed and not untracked
    status = b"" if clean else b"changed"
    diff = b"" if not changed else b"diff"
    raw_paths = tuple(sorted({"other.py", "src/allowed.py", "z.py", *changed}))
    tracked_worktree_files = tuple(
        TrackedWorktreeFile(
            path=path,
            mode="100644",
            content_sha256=canonical_sha256(
                f"{path}:{'changed' if path in changed else 'baseline'}".encode()
            ),
        )
        for path in raw_paths
    )
    tracked_index_entries = tuple(
        TrackedIndexEntry(
            path=path,
            mode="100644",
            object_id=canonical_sha256(f"{path}:index-baseline".encode()),
        )
        for path in raw_paths
    )
    return GitSnapshot(
        repository_id=repository_id,
        head=head,
        status_sha256=canonical_sha256(status),
        tracked_diff_sha256=canonical_sha256(diff),
        tracked_changed_paths=changed,
        all_untracked_paths=untracked,
        tracked_index_entries=tracked_index_entries,
        tracked_worktree_files=tracked_worktree_files,
        clean=clean,
        stability_samples=2,
    )


def _contract(
    baseline: GitSnapshot,
    *,
    allowed: tuple[str, ...] = ("src/allowed.py",),
) -> RunContract:
    return build_run_contract(
        run_id="run-1",
        baseline_snapshot=baseline,
        allowed_tracked_paths=allowed,
        verification_label="pytest",
    )


def _events(
    *,
    claim_text: str = "READY_FOR_REVIEW",
    terminal: str = "turn.completed",
) -> list[dict[str, object]]:
    return [
        {"type": "thread.started", "thread_id": "thread-1"},
        {"type": "turn.started"},
        {
            "type": "item.completed",
            "item": {
                "id": "item-1",
                "type": "agent_message",
                "text": claim_text,
            },
        },
        {"type": terminal},
    ]


def _claim(state: ClaimState, snapshot: GitSnapshot | None = None) -> AgentClaim:
    bound = snapshot_sha256(snapshot) if state is ClaimState.READY_FOR_REVIEW else None
    return AgentClaim(
        provider="codex",
        run_id="run-1",
        thread_id="thread-1",
        stream_closed=state is not ClaimState.PENDING,
        state=state,
        event_stream_sha256="3" * 64,
        claim_text="READY_FOR_REVIEW" if bound else None,
        bound_snapshot_sha256=bound,
        reason_codes=(state.value.upper(),),
    )


def _result(*, status: str = "success", exit_code: int | None = 0) -> VerificationRunResult:
    return VerificationRunResult(
        command_label="pytest",
        status=status,
        exit_code=exit_code,
        duration_ms=1,
    )


def _receipt(
    claim: AgentClaim,
    snapshot: GitSnapshot,
    *,
    status: str = "success",
    exit_code: int | None = 0,
) -> VerificationReceipt:
    return build_verification_receipt(
        verification_result=_result(status=status, exit_code=exit_code),
        claim=claim,
        post_verification_snapshot=snapshot,
    )


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        text=True,
        capture_output=True,
    )


def _init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.name", "RepoPilot Test")
    _git(repo, "config", "user.email", "repopilot@example.invalid")
    (repo / "tracked.txt").write_text("baseline\n", encoding="utf-8")
    _git(repo, "add", "tracked.txt")
    _git(repo, "commit", "-qm", "baseline")
    return repo


def test_contract_is_immutable_and_binds_clean_baseline_and_command() -> None:
    baseline = _snapshot()
    contract = _contract(baseline)

    assert contract.baseline_snapshot_sha256 == snapshot_sha256(baseline)
    assert contract.allowed_tracked_paths == ("src/allowed.py",)
    assert len(contract.verification_argv_sha256) == 64
    with pytest.raises(FrozenInstanceError):
        contract.run_id = "changed"  # type: ignore[misc]


@pytest.mark.parametrize(
    "allowed",
    [
        ("/absolute.py",),
        ("../escape.py",),
        ("a/./b.py",),
        ("a\\b.py",),
        ("same.py", "same.py"),
        ("b.py", "a.py"),
    ],
)
def test_contract_rejects_unsafe_duplicate_or_unsorted_paths(
    allowed: tuple[str, ...],
) -> None:
    with pytest.raises(ValueError):
        _contract(_snapshot(), allowed=allowed)


def test_contract_rejects_dirty_or_inconsistent_baseline() -> None:
    with pytest.raises(ValueError):
        _contract(_snapshot(changed=("old.py",)))

    clean = _snapshot()
    with pytest.raises(ValueError):
        replace(clean, clean=False)


def test_contract_rejects_unknown_or_resolved_command_drift(monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(ValueError):
        build_run_contract(
            run_id="run-1",
            baseline_snapshot=_snapshot(),
            allowed_tracked_paths=("src/allowed.py",),
            verification_label="arbitrary shell",
        )

    contract = _contract(_snapshot())
    monkeypatch.setattr(
        "app.supervision.contracts.command_argv",
        lambda _label: ["python", "different.py"],
    )
    decision = evaluate_governed_run(
        contract,
        _snapshot(),
        _snapshot(),
        _claim(ClaimState.PENDING),
    )
    assert decision.outcome is DecisionOutcome.INTERVENE
    assert decision.reason_codes == ("VERIFICATION_COMMAND_MISMATCH",)


def test_direct_constructor_and_replace_cannot_bypass_claim_invariants() -> None:
    with pytest.raises(ValueError):
        AgentClaim(
            provider="codex",
            run_id="run-1",
            thread_id="thread-1",
            stream_closed=False,
            state=ClaimState.READY_FOR_REVIEW,
            event_stream_sha256="3" * 64,
            claim_text="READY_FOR_REVIEW",
            bound_snapshot_sha256="4" * 64,
            reason_codes=("READY_FOR_REVIEW",),
        )

    ready = _claim(ClaimState.READY_FOR_REVIEW, _snapshot(changed=("src/allowed.py",)))
    with pytest.raises(ValueError):
        replace(ready, bound_snapshot_sha256=None)


def test_codex_adapter_distinguishes_open_prefix_and_exact_completion() -> None:
    open_claim = adapt_codex_events(
        run_id="run-1",
        events=_events()[:-1],
        stream_closed=False,
    )
    assert open_claim.state is ClaimState.PENDING
    assert open_claim.thread_id == "thread-1"

    completion = _snapshot(changed=("src/allowed.py",))
    ready = adapt_codex_events(
        run_id="run-1",
        events=_events(),
        stream_closed=True,
        completion_snapshot_sha256=snapshot_sha256(completion),
    )
    assert ready.state is ClaimState.READY_FOR_REVIEW
    assert ready.claim_text == "READY_FOR_REVIEW"
    assert ready.bound_snapshot_sha256 == snapshot_sha256(completion)


@pytest.mark.parametrize(
    ("events", "expected"),
    [
        (_events()[:-1], ClaimState.NOT_OBSERVED),
        (_events(claim_text="done"), ClaimState.NOT_OBSERVED),
        (_events(claim_text="done", terminal="turn.failed"), ClaimState.FAILED),
        (_events(terminal="turn.failed"), ClaimState.INVALID),
        (_events() + [{"type": "item.completed"}], ClaimState.INVALID),
        (_events() + [{"type": "turn.failed"}], ClaimState.INVALID),
        (
            [{"type": "future.event"}, *_events()],
            ClaimState.INVALID,
        ),
        (
            [{"type": "item.started"}, *_events()],
            ClaimState.INVALID,
        ),
        ([{"type": "turn.started"}, {"type": "turn.completed"}], ClaimState.INVALID),
        (
            [
                {"type": "thread.started", "thread_id": "thread-1"},
                {"type": "thread.started", "thread_id": "thread-2"},
                {"type": "turn.started"},
                {"type": "turn.completed"},
            ],
            ClaimState.INVALID,
        ),
        (
            [
                {"type": "thread.started", "thread_id": " "},
                {"type": "turn.started"},
                {"type": "turn.completed"},
            ],
            ClaimState.INVALID,
        ),
        (
            _events()[:-1]
            + [_events()[2], {"type": "turn.completed"}],
            ClaimState.INVALID,
        ),
    ],
)
def test_codex_adapter_fails_closed_for_missing_or_ambiguous_evidence(
    events: list[dict[str, object]], expected: ClaimState
) -> None:
    claim = adapt_codex_events(
        run_id="run-1",
        events=events,
        stream_closed=True,
        completion_snapshot_sha256="4" * 64,
    )
    assert claim.state is expected
    assert claim.reason_codes


def test_codex_adapter_requires_snapshot_for_exact_ready_claim() -> None:
    claim = adapt_codex_events(
        run_id="run-1",
        events=_events(),
        stream_closed=True,
    )
    assert claim.state is ClaimState.INVALID
    assert claim.reason_codes == ("COMPLETION_SNAPSHOT_NOT_OBSERVED",)


def test_archived_real_event_shape_is_consumed_without_elevating_provenance() -> None:
    observation = json.loads(ARCHIVED_OBSERVATION.read_text(encoding="utf-8"))
    claim = adapt_codex_events(
        run_id="archive-regression-only",
        events=observation["event_stream"],
        stream_closed=True,
        completion_snapshot_sha256="4" * 64,
    )
    assert claim.state is ClaimState.READY_FOR_REVIEW

    baseline = _snapshot()
    current = _snapshot(changed=("src/allowed.py",))
    contract = build_run_contract(
        run_id="archive-regression-only",
        baseline_snapshot=baseline,
        allowed_tracked_paths=("src/allowed.py",),
        verification_label="pytest",
    )
    claim = replace(claim, bound_snapshot_sha256=snapshot_sha256(current))
    decision = evaluate_governed_run(contract, baseline, current, claim, _receipt(claim, current))
    assert decision.source_provenance == "unverified"
    assert decision.task_complete is False
    assert decision.product_acceptance is False
    assert decision.git_delivery_authorized is False


@pytest.mark.parametrize(
    ("state", "changed", "receipt_kind", "outcome"),
    [
        (ClaimState.PENDING, False, "none", DecisionOutcome.CONTINUE),
        (ClaimState.PENDING, True, "none", DecisionOutcome.CONTINUE),
        (ClaimState.FAILED, False, "none", DecisionOutcome.NEEDS_HUMAN),
        (ClaimState.NOT_OBSERVED, False, "none", DecisionOutcome.NEEDS_HUMAN),
        (ClaimState.INVALID, False, "none", DecisionOutcome.INTERVENE),
        (ClaimState.READY_FOR_REVIEW, False, "none", DecisionOutcome.INTERVENE),
        (ClaimState.READY_FOR_REVIEW, True, "none", DecisionOutcome.NEEDS_HUMAN),
        (ClaimState.READY_FOR_REVIEW, True, "failed", DecisionOutcome.NEEDS_HUMAN),
        (ClaimState.READY_FOR_REVIEW, True, "passed", DecisionOutcome.READY_FOR_REVIEW),
    ],
)
def test_evaluator_total_claim_change_receipt_matrix(
    state: ClaimState,
    changed: bool,
    receipt_kind: str,
    outcome: DecisionOutcome,
) -> None:
    baseline = _snapshot()
    current = _snapshot(changed=("src/allowed.py",)) if changed else baseline
    contract = _contract(baseline)
    claim = _claim(state, current if state is ClaimState.READY_FOR_REVIEW else None)
    receipt = None
    if receipt_kind == "passed":
        receipt = _receipt(claim, current)
    elif receipt_kind == "failed":
        receipt = _receipt(claim, current, status="failed", exit_code=1)

    decision = evaluate_governed_run(contract, baseline, current, claim, receipt)

    assert decision.outcome is outcome
    assert decision.task_complete is False
    assert decision.product_acceptance is False
    assert decision.git_delivery_authorized is False
    assert decision.source_provenance == "unverified"
    assert decision.snapshot_continuity == "stable_endpoint_samples_only"


@pytest.mark.parametrize(
    ("mutation", "reason"),
    [
        ("untracked", "UNTRACKED_PATHS_NOT_ALLOWED"),
        ("out_of_scope", "OUT_OF_SCOPE_TRACKED_PATH"),
        ("repo", "REPOSITORY_MISMATCH"),
        ("head", "HEAD_MISMATCH"),
        ("claim_snapshot", "CLAIM_SNAPSHOT_MISMATCH"),
        ("receipt_run", "RECEIPT_CORRELATION_MISMATCH"),
        ("receipt_thread", "RECEIPT_CORRELATION_MISMATCH"),
        ("receipt_provider", "RECEIPT_CORRELATION_MISMATCH"),
        ("receipt_event", "RECEIPT_CORRELATION_MISMATCH"),
        ("receipt_claim", "RECEIPT_CORRELATION_MISMATCH"),
        ("receipt_label", "VERIFICATION_COMMAND_MISMATCH"),
        ("receipt_argv", "VERIFICATION_COMMAND_MISMATCH"),
        ("receipt_bound", "RECEIPT_SNAPSHOT_MISMATCH"),
        ("receipt_post", "RECEIPT_SNAPSHOT_MISMATCH"),
    ],
)
def test_evaluator_intervenes_on_scope_identity_or_snapshot_conflict(
    mutation: str, reason: str
) -> None:
    baseline = _snapshot()
    current = _snapshot(changed=("src/allowed.py",))
    contract = _contract(baseline)
    claim = _claim(ClaimState.READY_FOR_REVIEW, current)
    receipt = _receipt(claim, current)

    if mutation == "untracked":
        current = _snapshot(untracked=("ignored.log",))
    elif mutation == "out_of_scope":
        current = _snapshot(changed=("other.py",))
    elif mutation == "repo":
        current = _snapshot(changed=("src/allowed.py",), repository_id="5" * 64)
    elif mutation == "head":
        current = _snapshot(changed=("src/allowed.py",), head="6" * 40)
    elif mutation == "claim_snapshot":
        claim = replace(claim, bound_snapshot_sha256="7" * 64)
    elif mutation == "receipt_run":
        receipt = replace(receipt, run_id="other-run")
    elif mutation == "receipt_thread":
        receipt = replace(receipt, thread_id="other-thread")
    elif mutation == "receipt_provider":
        receipt = replace(receipt, provider="other-provider")
    elif mutation == "receipt_event":
        receipt = replace(receipt, event_stream_sha256="8" * 64)
    elif mutation == "receipt_claim":
        receipt = replace(receipt, claim_sha256="8" * 64)
    elif mutation == "receipt_label":
        receipt = replace(receipt, verification_label="ruff")
    elif mutation == "receipt_argv":
        receipt = replace(receipt, verification_argv_sha256="9" * 64)
    elif mutation == "receipt_bound":
        receipt = replace(receipt, bound_snapshot_sha256="9" * 64)
    elif mutation == "receipt_post":
        receipt = replace(
            receipt,
            post_verification_snapshot=_snapshot(changed=("src/allowed.py", "z.py")),
        )

    decision = evaluate_governed_run(contract, baseline, current, claim, receipt)
    assert decision.outcome is DecisionOutcome.INTERVENE
    assert decision.reason_codes == (reason,)


def test_conflict_precedence_beats_premature_receipt() -> None:
    baseline = _snapshot()
    current = _snapshot(untracked=("ignored.log",))
    contract = _contract(baseline)
    ready = _claim(ClaimState.READY_FOR_REVIEW, current)
    premature_claim = _claim(ClaimState.PENDING)
    receipt = _receipt(ready, current)

    decision = evaluate_governed_run(contract, baseline, current, premature_claim, receipt)
    assert decision.reason_codes == ("UNTRACKED_PATHS_NOT_ALLOWED",)


def test_evaluator_detects_raw_mode_only_scope_change() -> None:
    baseline = _snapshot()
    raw_files = tuple(
        replace(item, mode="100755") if item.path == "other.py" else item
        for item in baseline.tracked_worktree_files
    )
    current = replace(baseline, tracked_worktree_files=raw_files)
    decision = evaluate_governed_run(
        _contract(baseline),
        baseline,
        current,
        _claim(ClaimState.PENDING),
    )
    assert decision.outcome is DecisionOutcome.INTERVENE
    assert decision.reason_codes == ("OUT_OF_SCOPE_TRACKED_PATH",)


def test_evaluator_accepts_allowed_raw_only_change_as_evidenced_change() -> None:
    baseline = _snapshot()
    raw_files = tuple(
        replace(item, content_sha256="a" * 64)
        if item.path == "src/allowed.py"
        else item
        for item in baseline.tracked_worktree_files
    )
    current = replace(baseline, tracked_worktree_files=raw_files)
    contract = _contract(baseline)
    claim = _claim(ClaimState.READY_FOR_REVIEW, current)
    decision = evaluate_governed_run(
        contract,
        baseline,
        current,
        claim,
        _receipt(claim, current),
    )
    assert decision.outcome is DecisionOutcome.READY_FOR_REVIEW


def test_premature_receipt_intervenes() -> None:
    baseline = _snapshot()
    current = _snapshot(changed=("src/allowed.py",))
    contract = _contract(baseline)
    ready = _claim(ClaimState.READY_FOR_REVIEW, current)
    pending = _claim(ClaimState.PENDING)
    receipt = replace(_receipt(ready, current), claim_sha256=claim_sha256(pending))
    decision = evaluate_governed_run(
        contract,
        baseline,
        current,
        pending,
        receipt,
    )
    assert decision.reason_codes == ("PREMATURE_VERIFICATION_RECEIPT",)


def test_receipt_binds_claim_event_command_result_and_full_snapshot() -> None:
    snapshot = _snapshot(changed=("src/allowed.py",))
    claim = _claim(ClaimState.READY_FOR_REVIEW, snapshot)
    receipt = _receipt(claim, snapshot)

    assert receipt.claim_sha256 == claim_sha256(claim)
    assert receipt.event_stream_sha256 == claim.event_stream_sha256
    assert receipt.bound_snapshot_sha256 == snapshot_sha256(snapshot)
    assert receipt.post_verification_snapshot == snapshot
    assert len(receipt.verification_result_sha256) == 64

    with pytest.raises(ValueError):
        replace(receipt, verification_status="success", exit_code=None)


@POSIX_ONLY
def test_git_collector_captures_tracked_rename_and_all_untracked(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    (repo / ".gitignore").write_text("ignored.log\n", encoding="utf-8")
    _git(repo, "add", ".gitignore")
    _git(repo, "commit", "-qm", "ignore")
    _git(repo, "mv", "tracked.txt", "renamed.txt")
    (repo / "ordinary.tmp").write_text("ordinary\n", encoding="utf-8")
    (repo / "ignored.log").write_text("ignored\n", encoding="utf-8")

    before_head = _git(repo, "rev-parse", "HEAD").stdout.strip()
    before_status = _git(
        repo,
        "status",
        "--porcelain=v1",
        "-z",
        "--untracked-files=all",
        "--ignored=matching",
    ).stdout
    snapshot = collect_git_snapshot(repo)
    after_head = _git(repo, "rev-parse", "HEAD").stdout.strip()
    after_status = _git(
        repo,
        "status",
        "--porcelain=v1",
        "-z",
        "--untracked-files=all",
        "--ignored=matching",
    ).stdout

    assert snapshot.clean is False
    assert snapshot.stability_samples == 2
    assert snapshot.tracked_changed_paths == ("renamed.txt", "tracked.txt")
    assert snapshot.all_untracked_paths == ("ignored.log", "ordinary.tmp")
    assert after_head == before_head
    assert after_status == before_status


@POSIX_ONLY
def test_git_collector_ignores_inherited_git_state(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = _init_repo(tmp_path)
    monkeypatch.setenv("GIT_DIR", str(tmp_path / "attacker"))
    monkeypatch.setenv("GIT_WORK_TREE", str(tmp_path))
    monkeypatch.setenv("GIT_EXTERNAL_DIFF", "should-not-run")

    snapshot = collect_git_snapshot(repo)

    assert snapshot.clean is True
    env = _controlled_git_env()
    assert env["PATH"] == os.defpath
    assert "GIT_DIR" not in env
    assert "GIT_WORK_TREE" not in env
    assert "GIT_EXTERNAL_DIFF" not in env
    assert env["GIT_OPTIONAL_LOCKS"] == "0"
    assert env["GIT_TERMINAL_PROMPT"] == "0"


@POSIX_ONLY
def test_git_collector_does_not_resolve_git_from_inherited_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = _init_repo(tmp_path)
    marker = tmp_path / "fake-git-ran"
    fake_git = repo / "git"
    fake_git.write_text(f"#!/bin/sh\ntouch {marker}\nexit 1\n", encoding="utf-8")
    fake_git.chmod(0o755)
    monkeypatch.setenv("PATH", f"{repo}{os.pathsep}.")

    snapshot = collect_git_snapshot(repo)

    assert snapshot.all_untracked_paths == ("git",)
    assert not marker.exists()
    assert not Path(snapshot_module._resolve_git_executable(repo)).is_relative_to(repo)


def test_git_collector_fails_before_spawn_without_process_tree_isolation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spawned = False

    def unexpected_spawn(*_args: object, **_kwargs: object) -> None:
        nonlocal spawned
        spawned = True

    monkeypatch.setattr(snapshot_module, "_process_isolation_supported", lambda: False)
    monkeypatch.setattr(snapshot_module.subprocess, "Popen", unexpected_spawn)

    with pytest.raises(GitSnapshotCollectionError, match="PROCESS_ISOLATION_UNAVAILABLE"):
        collect_git_snapshot(tmp_path)
    assert spawned is False


@POSIX_ONLY
def test_git_collector_rejects_input_and_tracked_symlinks(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    alias = tmp_path / "alias"
    alias.symlink_to(repo, target_is_directory=True)
    with pytest.raises(GitSnapshotCollectionError, match="SYMLINK_TRAVERSAL"):
        collect_git_snapshot(alias)

    (repo / "tracked-link").symlink_to("tracked.txt")
    _git(repo, "add", "tracked-link")
    _git(repo, "commit", "-qm", "link")
    with pytest.raises(GitSnapshotCollectionError, match="TRACKED_SYMLINK_NOT_SUPPORTED"):
        collect_git_snapshot(repo)


@POSIX_ONLY
def test_git_collector_rejects_regular_tracked_path_replaced_by_symlink(
    tmp_path: Path,
) -> None:
    repo = _init_repo(tmp_path)
    outside = tmp_path / "outside.txt"
    outside.write_text("outside\n", encoding="utf-8")
    (repo / "tracked.txt").unlink()
    (repo / "tracked.txt").symlink_to(outside)

    with pytest.raises(
        GitSnapshotCollectionError,
        match="TRACKED_WORKTREE_SYMLINK_NOT_SUPPORTED",
    ):
        collect_git_snapshot(repo)


@POSIX_ONLY
def test_git_collector_rejects_gitlink_before_content_reads(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    nested = repo / "nested"
    nested.mkdir()
    _git(nested, "init", "-q")
    _git(nested, "config", "user.name", "RepoPilot Test")
    _git(nested, "config", "user.email", "repopilot@example.invalid")
    (nested / "child.txt").write_text("child\n", encoding="utf-8")
    _git(nested, "add", "child.txt")
    _git(nested, "commit", "-qm", "child")
    _git(repo, "add", "nested")
    _git(repo, "commit", "-qm", "gitlink")

    with pytest.raises(GitSnapshotCollectionError, match="GITLINK_NOT_SUPPORTED"):
        collect_git_snapshot(repo)


@POSIX_ONLY
@pytest.mark.parametrize("scope", ["--local", "--worktree"])
@pytest.mark.parametrize("driver", ["clean", "process"])
def test_git_collector_rejects_clean_filter_without_executing_it(
    tmp_path: Path, scope: str, driver: str
) -> None:
    repo = _init_repo(tmp_path)
    marker = tmp_path / "helper-ran"
    if scope == "--worktree":
        _git(repo, "config", "extensions.worktreeConfig", "true")
    _git(repo, "config", scope, f"filter.evil.{driver}", f"touch {marker}")

    with pytest.raises(GitSnapshotCollectionError, match="CONTENT_FILTER_NOT_SUPPORTED"):
        collect_git_snapshot(repo)
    assert not marker.exists()


@POSIX_ONLY
def test_git_collector_rejects_non_root_and_non_repository(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    child = repo / "child"
    child.mkdir()
    with pytest.raises(GitSnapshotCollectionError, match="REPOSITORY_ROOT_MISMATCH"):
        collect_git_snapshot(child)
    with pytest.raises(GitSnapshotCollectionError, match="NOT_A_GIT_REPOSITORY"):
        collect_git_snapshot(tmp_path)


@pytest.mark.parametrize(
    "payload",
    [b"missing-terminator", b"a\0\0", b"../escape\0", b"a\\b\0", b"\xff\0"],
)
def test_git_collector_rejects_malformed_nul_path_output(payload: bytes) -> None:
    with pytest.raises(GitSnapshotCollectionError, match="MALFORMED_NUL_PATH_OUTPUT"):
        snapshot_module._parse_nul_paths(payload)


def test_git_collector_uses_fixed_argv_and_sanitized_child_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    observed: dict[str, object] = {}

    def fake_run(
        argv: list[str],
        *,
        cwd: Path,
        env: dict[str, str],
        timeout_seconds: float,
        output_cap_bytes: int,
    ) -> tuple[bytes, bytes, int]:
        observed.update(argv=argv, cwd=cwd, env=env)
        assert timeout_seconds == snapshot_module.DEFAULT_COMMAND_TIMEOUT_SECONDS
        assert output_cap_bytes == snapshot_module.DEFAULT_OUTPUT_CAP_BYTES
        return b"ok", b"", 0

    monkeypatch.setattr(
        snapshot_module,
        "_resolve_git_executable",
        lambda _cwd: "/fixed/git",
    )
    monkeypatch.setattr(snapshot_module, "_run_bounded_process", fake_run)
    stdout, returncode = snapshot_module._run_git_command(tmp_path, ("status", "--porcelain=v1"))

    assert stdout == b"ok"
    assert returncode == 0
    assert observed["argv"] == [
        "/fixed/git",
        "-c",
        "core.fsmonitor=false",
        "-c",
        "core.untrackedCache=false",
        "-c",
        "diff.external=",
        "status",
        "--porcelain=v1",
    ]
    env = observed["env"]
    assert isinstance(env, dict)
    assert all(not key.startswith("GIT_") or key in {
        "GIT_OPTIONAL_LOCKS",
        "GIT_TERMINAL_PROMPT",
        "GIT_PAGER",
        "GIT_CONFIG_NOSYSTEM",
        "GIT_CONFIG_SYSTEM",
        "GIT_CONFIG_GLOBAL",
        "GIT_ATTR_NOSYSTEM",
    } for key in env)


@POSIX_ONLY
def test_git_collector_disables_fsmonitor_and_textconv_helpers(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    fsmonitor_marker = tmp_path / "fsmonitor-ran"
    textconv_marker = tmp_path / "textconv-ran"
    (repo / ".gitattributes").write_text("tracked.txt diff=evil\n", encoding="utf-8")
    _git(repo, "add", ".gitattributes")
    _git(repo, "commit", "-qm", "attributes")
    _git(repo, "config", "core.fsmonitor", f"touch {fsmonitor_marker}")
    _git(repo, "config", "diff.evil.textconv", f"touch {textconv_marker}")
    (repo / "tracked.txt").write_text("changed\n", encoding="utf-8")

    snapshot = collect_git_snapshot(repo)

    assert snapshot.tracked_changed_paths == ("tracked.txt",)
    assert not fsmonitor_marker.exists()
    assert not textconv_marker.exists()


@POSIX_ONLY
def test_git_collector_binds_raw_mode_ignored_by_git_filemode(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _git(repo, "config", "core.filemode", "false")
    baseline = collect_git_snapshot(repo)
    (repo / "tracked.txt").chmod(0o755)

    current = collect_git_snapshot(repo)

    assert current.clean is True
    assert current.tracked_changed_paths == ()
    assert snapshot_sha256(current) != snapshot_sha256(baseline)
    decision = evaluate_governed_run(
        build_run_contract(
            run_id="run-1",
            baseline_snapshot=baseline,
            allowed_tracked_paths=("allowed.txt",),
            verification_label="pytest",
        ),
        baseline,
        current,
        _claim(ClaimState.PENDING),
    )
    assert decision.reason_codes == ("OUT_OF_SCOPE_TRACKED_PATH",)


@POSIX_ONLY
def test_git_collector_binds_masked_staged_index_blob_and_enforces_scope(
    tmp_path: Path,
) -> None:
    repo = _init_repo(tmp_path)
    (repo / "allowed.txt").write_text("allowed baseline\n", encoding="utf-8")
    _git(repo, "add", "allowed.txt")
    _git(repo, "commit", "-qm", "add allowed path")
    baseline = collect_git_snapshot(repo)
    contract = build_run_contract(
        run_id="run-1",
        baseline_snapshot=baseline,
        allowed_tracked_paths=("allowed.txt",),
        verification_label="pytest",
    )

    (repo / "tracked.txt").write_text("staged one\n", encoding="utf-8")
    _git(repo, "add", "tracked.txt")
    (repo / "tracked.txt").write_text("baseline\n", encoding="utf-8")
    (repo / "allowed.txt").write_text("allowed changed\n", encoding="utf-8")
    first = collect_git_snapshot(repo)

    (repo / "tracked.txt").write_text("staged two\n", encoding="utf-8")
    _git(repo, "add", "tracked.txt")
    (repo / "tracked.txt").write_text("baseline\n", encoding="utf-8")
    second = collect_git_snapshot(repo)

    assert first.tracked_changed_paths == ("allowed.txt",)
    assert second.tracked_changed_paths == ("allowed.txt",)
    assert first.tracked_worktree_files == second.tracked_worktree_files
    assert first.tracked_index_entries != second.tracked_index_entries
    assert snapshot_sha256(first) != snapshot_sha256(second)
    decision = evaluate_governed_run(
        contract,
        baseline,
        first,
        _claim(ClaimState.PENDING),
    )
    assert decision.reason_codes == ("OUT_OF_SCOPE_TRACKED_PATH",)

    wide_contract = build_run_contract(
        run_id="run-1",
        baseline_snapshot=baseline,
        allowed_tracked_paths=("allowed.txt", "tracked.txt"),
        verification_label="pytest",
    )
    ready = _claim(ClaimState.READY_FOR_REVIEW, first)
    receipt = replace(_receipt(ready, first), post_verification_snapshot=second)
    drift = evaluate_governed_run(wide_contract, baseline, first, ready, receipt)
    assert drift.reason_codes == ("RECEIPT_SNAPSHOT_MISMATCH",)


@POSIX_ONLY
def test_git_collector_fails_closed_for_git_normalized_raw_eol_change(
    tmp_path: Path,
) -> None:
    repo = _init_repo(tmp_path)
    (repo / ".gitattributes").write_text("tracked.txt text eol=lf\n", encoding="utf-8")
    _git(repo, "add", ".gitattributes")
    _git(repo, "commit", "-qm", "attributes")
    collect_git_snapshot(repo)
    (repo / "tracked.txt").write_bytes(b"baseline\r\n")

    with pytest.raises(GitSnapshotCollectionError, match="INCONSISTENT_GIT_SNAPSHOT"):
        collect_git_snapshot(repo)


@POSIX_ONLY
def test_git_collector_rejects_observable_two_sample_drift(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _init_repo(tmp_path)
    original = snapshot_module._collect_sample
    calls = 0

    def changing_sample(cwd: Path, git_executable: str) -> object:
        nonlocal calls
        sample = original(cwd, git_executable)
        calls += 1
        if calls == 1:
            (repo / "tracked.txt").write_text("changed between samples\n", encoding="utf-8")
        return sample

    monkeypatch.setattr(snapshot_module, "_collect_sample", changing_sample)
    with pytest.raises(
        GitSnapshotCollectionError,
        match="REPOSITORY_CHANGED_DURING_COLLECTION",
    ):
        collect_git_snapshot(repo)


@POSIX_ONLY
def test_bounded_process_enforces_timeout_output_cap_and_closed_stdin(tmp_path: Path) -> None:
    with pytest.raises(GitSnapshotCollectionError, match="COMMAND_TIMED_OUT"):
        _run_bounded_process(
            [sys.executable, "-c", "import time; time.sleep(10)"],
            cwd=tmp_path,
            env={"PATH": os.environ.get("PATH", "")},
            timeout_seconds=0.05,
            output_cap_bytes=1024,
        )

    with pytest.raises(GitSnapshotCollectionError, match="COMMAND_OUTPUT_LIMIT_EXCEEDED"):
        _run_bounded_process(
            [sys.executable, "-c", "print('x' * 10000)"],
            cwd=tmp_path,
            env={"PATH": os.environ.get("PATH", "")},
            timeout_seconds=2,
            output_cap_bytes=128,
        )

    stdout, _stderr, returncode = _run_bounded_process(
        [sys.executable, "-c", "import sys; print(sys.stdin.read())"],
        cwd=tmp_path,
        env={"PATH": os.environ.get("PATH", "")},
        timeout_seconds=2,
        output_cap_bytes=1024,
    )
    assert stdout == b"\n"
    assert returncode == 0


@POSIX_ONLY
def test_bounded_process_timeout_cleans_up_its_process_group(tmp_path: Path) -> None:
    marker = tmp_path / "orphan-marker"
    child_code = (
        "import pathlib,time; time.sleep(0.6); "
        f"pathlib.Path({str(marker)!r}).write_text('orphan', encoding='utf-8')"
    )
    parent_code = (
        "import subprocess,sys,time; "
        f"subprocess.Popen([sys.executable, '-c', {child_code!r}]); "
        "time.sleep(10)"
    )
    with pytest.raises(GitSnapshotCollectionError, match="COMMAND_TIMED_OUT"):
        _run_bounded_process(
            [sys.executable, "-c", parent_code],
            cwd=tmp_path,
            env={"PATH": os.environ.get("PATH", "")},
            timeout_seconds=0.2,
            output_cap_bytes=1024,
        )
    time.sleep(0.7)
    assert not marker.exists()


@POSIX_ONLY
def test_bounded_process_rejects_and_cleans_lingering_descendant(tmp_path: Path) -> None:
    marker = tmp_path / "lingering-marker"
    child_code = (
        "import pathlib,time; time.sleep(0.8); "
        f"pathlib.Path({str(marker)!r}).write_text('orphan', encoding='utf-8')"
    )
    parent_code = (
        "import subprocess,sys; "
        f"subprocess.Popen([sys.executable, '-c', {child_code!r}])"
    )
    with pytest.raises(
        GitSnapshotCollectionError,
        match="COMMAND_PROCESS_TREE_REMAINED",
    ):
        _run_bounded_process(
            [sys.executable, "-c", parent_code],
            cwd=tmp_path,
            env={"PATH": os.environ.get("PATH", "")},
            timeout_seconds=2,
            output_cap_bytes=1024,
        )
    time.sleep(0.9)
    assert not marker.exists()


def test_governance_decision_constructor_enforces_claim_ceiling() -> None:
    with pytest.raises(ValueError):
        GovernanceDecision(
            outcome=DecisionOutcome.READY_FOR_REVIEW,
            reason_codes=("VERIFICATION_PASSED",),
            task_complete=True,
        )
