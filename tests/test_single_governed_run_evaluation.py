from __future__ import annotations

import hashlib
import io
import json
import os
import subprocess
from dataclasses import replace
from pathlib import Path

import pytest

import scripts.evaluate_single_governed_run as evaluation_module
from app.supervision import collect_git_snapshot
from app.verification.runner import (
    VerificationRunResult,
    run_whitelisted_verification,
)
from scripts.evaluate_single_governed_run import (
    BASE_README_SHA256,
    EXPECTED_README_FIRST_LINE,
    EXPECTED_README_SHA256,
    FROZEN_BASE_HEAD,
    OBSERVATION_SCHEMA,
    PROJECT_ROOT,
    STATIC_PROMPT,
    ExperimentStatus,
    ObservationFailure,
    assert_stage_readme_unchanged,
    parse_host_task_observation,
    prepare_host_task,
)

THREAD_ID = "thread-codex-app-fixed"


def _git(repo: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return completed.stdout.strip()


def _base_readme() -> bytes:
    value = (PROJECT_ROOT / "README.md").read_bytes()
    assert hashlib.sha256(value).hexdigest() == BASE_README_SHA256
    return value


def _expected_readme() -> bytes:
    baseline = _base_readme()
    value = EXPECTED_README_FIRST_LINE + baseline[len(b"# RepoPilot\n") :]
    assert hashlib.sha256(value).hexdigest() == EXPECTED_README_SHA256
    return value


def _fixture_worktree(tmp_path: Path) -> tuple[Path, Path, object]:
    primary = tmp_path / "primary"
    primary.mkdir(parents=True)
    (primary / "README.md").write_bytes(_base_readme())
    (primary / "probe.py").write_text("VALUE = 1\n", encoding="utf-8")
    (primary / ".gitignore").write_text(".ruff_cache/\n", encoding="utf-8")
    _git(primary, "init", "-q")
    _git(primary, "config", "user.name", "RepoPilot Test")
    _git(primary, "config", "user.email", "repopilot@example.invalid")
    _git(primary, "add", "README.md", "probe.py", ".gitignore")
    _git(primary, "commit", "-qm", "fixed baseline")
    task = tmp_path / "task"
    _git(primary, "worktree", "add", "--detach", str(task), "HEAD")
    baseline = collect_git_snapshot(task)
    assert baseline.clean
    return primary, task, baseline


def _observation(
    *,
    thread_id: str = THREAD_ID,
    terminal_status: str = "completed",
    final_text: str = "READY_FOR_REVIEW",
    schema_version: str = OBSERVATION_SCHEMA,
    extra: dict[str, object] | None = None,
) -> bytes:
    value: dict[str, object] = {
        "schema_version": schema_version,
        "thread_id": thread_id,
        "terminal_status": terminal_status,
        "final_text": final_text,
    }
    if extra:
        value.update(extra)
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
        + b"\n"
    )


def _bridge(tmp_path: Path):
    primary, task, baseline = _fixture_worktree(tmp_path)
    bridge = prepare_host_task(
        task,
        THREAD_ID,
        expected_head=baseline.head,
        stage_root=primary,
    )
    return primary, task, baseline, bridge


def test_positive_chain_uses_real_no_cache_runner_and_same_snapshot(
    tmp_path: Path,
) -> None:
    _, task, _, bridge = _bridge(tmp_path)
    (task / "README.md").write_bytes(_expected_readme())

    def observed_runner(repo: str | Path, label: str) -> VerificationRunResult:
        assert os.environ.get("RUFF_NO_CACHE") == "true"
        return run_whitelisted_verification(repo, label)

    summary = bridge.consume(
        _observation(),
        verification_runner=observed_runner,
    )

    assert summary.status is ExperimentStatus.NOT_OBSERVED
    assert summary.deterministic_chain_passed is True
    assert summary.reason_codes == (
        "MECHANICAL_CHAIN_READY_HOST_SOURCE_UNVERIFIED",
    )
    assert summary.decision_outcome == "ready_for_review"
    assert summary.decision_reason == "VERIFICATION_PASSED"
    assert summary.verification_status == "success"
    assert summary.completion_snapshot_sha256 == summary.post_snapshot_sha256
    assert summary.source_provenance == "host_observed_unverified"
    assert summary.host_task_observed is False
    assert summary.real_observation is False
    assert summary.task_complete is False
    assert summary.semantic_completion is False
    assert summary.human_review == "NOT_OBSERVED"
    assert summary.product_acceptance is False
    assert summary.runtime_integration is False
    assert summary.git_delivery_authorized is False
    assert summary.observation_sha256
    assert summary.claim_sha256
    assert summary.receipt_sha256
    assert not (task / ".ruff_cache").exists()
    assert (task / "README.md").read_bytes() == _expected_readme()
    with pytest.raises(ValueError, match="cannot self-prove"):
        replace(summary, real_observation=True)


@pytest.mark.parametrize(
    ("raw", "reason"),
    [
        (b"", "OBSERVATION_EMPTY"),
        (b"\xff", "OBSERVATION_UTF8_INVALID"),
        (b" {}\n", "OBSERVATION_TRAILING_DATA"),
        (_observation() + b"{}\n", "OBSERVATION_TRAILING_DATA"),
        (
            (
                b'{"schema_version":"repopilot.codex_app_task_observation/v1",'
                b'"thread_id":"thread-codex-app-fixed","thread_id":"other",'
                b'"terminal_status":"completed",'
                b'"final_text":"READY_FOR_REVIEW"}\n'
            ),
            "OBSERVATION_JSON_INVALID",
        ),
        (_observation(extra={"unexpected": True}), "OBSERVATION_SCHEMA_INVALID"),
        (
            _observation(schema_version="wrong"),
            "OBSERVATION_SCHEMA_INVALID",
        ),
        (_observation(thread_id="other"), "OBSERVATION_THREAD_MISMATCH"),
        (
            _observation(terminal_status="failed"),
            "OBSERVATION_TERMINAL_NOT_COMPLETED",
        ),
        (
            _observation(final_text="done"),
            "OBSERVATION_FINAL_TEXT_MISMATCH",
        ),
    ],
)
def test_observation_parser_fails_closed(raw: bytes, reason: str) -> None:
    with pytest.raises(ObservationFailure) as captured:
        parse_host_task_observation(raw, expected_thread_id=THREAD_ID)
    assert captured.value.code == reason


def test_observation_size_and_duplicate_consumption_fail_closed(
    tmp_path: Path,
) -> None:
    with pytest.raises(ObservationFailure) as oversized:
        parse_host_task_observation(
            b"x" * 32,
            expected_thread_id=THREAD_ID,
            max_bytes=16,
        )
    assert oversized.value.code == "OBSERVATION_OUTPUT_LIMIT_EXCEEDED"

    _, _, _, bridge = _bridge(tmp_path)
    with pytest.raises(ObservationFailure):
        bridge.consume(b"not-json")
    with pytest.raises(ObservationFailure) as duplicate:
        bridge.consume(_observation())
    assert duplicate.value.code == "OBSERVATION_DUPLICATE"


@pytest.mark.parametrize("trailing", [False, True])
def test_live_channel_accepts_one_record_and_rejects_trailing_record(
    monkeypatch: pytest.MonkeyPatch,
    trailing: bool,
) -> None:
    read_fd, write_fd = os.pipe()
    payload = _observation() + (b"{}\n" if trailing else b"")
    os.write(write_fd, payload)
    os.close(write_fd)
    binary = os.fdopen(read_fd, "rb")
    text = io.TextIOWrapper(binary, encoding="utf-8")
    monkeypatch.setattr(evaluation_module.sys, "stdin", text)
    try:
        if trailing:
            with pytest.raises(ObservationFailure) as captured:
                evaluation_module._read_single_observation()
            assert captured.value.code == "OBSERVATION_TRAILING_DATA"
        else:
            assert evaluation_module._read_single_observation() == _observation()
    finally:
        text.close()


def test_live_channel_rejects_unclosed_input(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    read_fd, write_fd = os.pipe()
    os.write(write_fd, _observation())
    binary = os.fdopen(read_fd, "rb")
    text = io.TextIOWrapper(binary, encoding="utf-8")
    monkeypatch.setattr(evaluation_module.sys, "stdin", text)
    try:
        with pytest.raises(ObservationFailure) as captured:
            evaluation_module._read_single_observation(timeout_seconds=0.01)
        assert captured.value.code == "OBSERVATION_CHANNEL_TIMEOUT"
    finally:
        os.close(write_fd)
        text.close()


def test_stage_readme_role_is_separate_and_bound_to_base_digest(
    tmp_path: Path,
) -> None:
    assert_stage_readme_unchanged(PROJECT_ROOT)
    fake_stage = tmp_path / "stage"
    fake_stage.mkdir()
    (fake_stage / "README.md").write_text("# Changed\n", encoding="utf-8")
    with pytest.raises(ObservationFailure) as captured:
        assert_stage_readme_unchanged(fake_stage)
    assert captured.value.code == "STAGE_README_MUTATED"


def test_prepare_requires_linked_clean_same_repository_worktree(
    tmp_path: Path,
) -> None:
    primary, task, baseline = _fixture_worktree(tmp_path)

    with pytest.raises(ObservationFailure) as primary_role:
        prepare_host_task(
            primary,
            THREAD_ID,
            expected_head=baseline.head,
            stage_root=primary,
        )
    assert primary_role.value.code == "TASK_WORKTREE_ROLE_COLLISION"

    (task / "handshake-drift.txt").write_text("drift\n", encoding="utf-8")
    with pytest.raises(ObservationFailure) as dirty:
        prepare_host_task(
            task,
            THREAD_ID,
            expected_head=baseline.head,
            stage_root=primary,
        )
    assert dirty.value.code == "BASELINE_NOT_CLEAN"


def test_worktree_registration_ignores_unrelated_prunable_record(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    live = tmp_path / "live"
    live.mkdir()
    missing = tmp_path / "missing"
    prunable = tmp_path / "prunable"
    prunable.mkdir()
    output = (
        f"worktree {live}\nHEAD {'1' * 40}\n\n"
        f"worktree {missing}\nHEAD {'2' * 40}\n"
        "prunable gitdir file points to non-existent location\n\n"
        f"worktree {prunable}\nHEAD {'3' * 40}\n"
        "prunable locked reason\n\n"
    ).encode()
    completed = subprocess.CompletedProcess(
        args=["git", "worktree", "list"],
        returncode=0,
        stdout=output,
        stderr=b"",
    )
    monkeypatch.setattr(
        evaluation_module.subprocess,
        "run",
        lambda *args, **kwargs: completed,
    )

    assert evaluation_module._registered_worktree_paths(live) == (
        live.resolve(),
    )


def test_prepare_rejects_wrong_head_and_repository_identity(
    tmp_path: Path,
) -> None:
    primary, task, baseline = _fixture_worktree(tmp_path / "first")
    with pytest.raises(ObservationFailure) as wrong_head:
        prepare_host_task(
            task,
            THREAD_ID,
            expected_head=FROZEN_BASE_HEAD,
            stage_root=primary,
        )
    assert wrong_head.value.code == "BASELINE_HEAD_MISMATCH"

    other_primary, _, _ = _fixture_worktree(tmp_path / "other")
    with pytest.raises(ObservationFailure) as wrong_repo:
        prepare_host_task(
            task,
            THREAD_ID,
            expected_head=baseline.head,
            stage_root=other_primary,
        )
    assert wrong_repo.value.code == "BASELINE_REPOSITORY_MISMATCH"


@pytest.mark.parametrize(
    ("mutation", "reason"),
    [
        ("wrong_readme", "COMPLETION_README_MISMATCH"),
        ("untracked", "COMPLETION_UNTRACKED_PATH"),
        ("other_tracked", "COMPLETION_SCOPE_MISMATCH"),
        ("index", "COMPLETION_INDEX_DRIFT"),
    ],
)
def test_completion_scope_and_bytes_fail_closed(
    tmp_path: Path,
    mutation: str,
    reason: str,
) -> None:
    _, task, _, bridge = _bridge(tmp_path)
    if mutation == "wrong_readme":
        (task / "README.md").write_bytes(_expected_readme() + b"x")
    else:
        (task / "README.md").write_bytes(_expected_readme())
    if mutation == "untracked":
        (task / "extra.txt").write_text("x\n", encoding="utf-8")
    elif mutation == "other_tracked":
        (task / "probe.py").write_text("VALUE = 2\n", encoding="utf-8")
    elif mutation == "index":
        _git(task, "add", "README.md")

    with pytest.raises(ObservationFailure) as captured:
        bridge.consume(_observation())
    assert captured.value.code == reason


def test_runner_before_snapshot_drift_fails_closed(tmp_path: Path) -> None:
    _, task, _, bridge = _bridge(tmp_path)
    (task / "README.md").write_bytes(_expected_readme())
    calls = 0

    def drifting_collector(repo: str | Path):
        nonlocal calls
        calls += 1
        if calls == 2:
            (Path(repo) / "late.txt").write_text("late\n", encoding="utf-8")
        return collect_git_snapshot(repo)

    with pytest.raises(ObservationFailure) as captured:
        bridge.consume(
            _observation(),
            snapshot_collector=drifting_collector,
        )
    assert captured.value.code == "RUNNER_BEFORE_SNAPSHOT_DRIFT"


def test_post_verification_snapshot_drift_fails_closed(tmp_path: Path) -> None:
    _, task, _, bridge = _bridge(tmp_path)
    (task / "README.md").write_bytes(_expected_readme())

    def drifting_runner(repo: str | Path, label: str) -> VerificationRunResult:
        result = run_whitelisted_verification(repo, label)
        (Path(repo) / "README.md").write_bytes(_expected_readme() + b"x")
        return result

    with pytest.raises(ObservationFailure) as captured:
        bridge.consume(
            _observation(),
            verification_runner=drifting_runner,
        )
    assert captured.value.code == "POST_VERIFICATION_SNAPSHOT_DRIFT"


def test_verifier_cache_write_and_failure_fail_closed(tmp_path: Path) -> None:
    _, task, _, bridge = _bridge(tmp_path)
    (task / "README.md").write_bytes(_expected_readme())

    def cache_writer(repo: str | Path, label: str) -> VerificationRunResult:
        (Path(repo) / ".ruff_cache").mkdir()
        return VerificationRunResult(
            command_label=label,
            status="success",
            exit_code=0,
            duration_ms=1,
        )

    with pytest.raises(ObservationFailure) as cache:
        bridge.consume(_observation(), verification_runner=cache_writer)
    assert cache.value.code == "VERIFIER_CACHE_WRITE"

    _, task2, _, bridge2 = _bridge(tmp_path / "second")
    (task2 / "README.md").write_bytes(_expected_readme())

    def failed_runner(repo: str | Path, label: str) -> VerificationRunResult:
        return VerificationRunResult(
            command_label=label,
            status="failed",
            exit_code=1,
            duration_ms=1,
        )

    with pytest.raises(ObservationFailure) as failed:
        bridge2.consume(_observation(), verification_runner=failed_runner)
    assert failed.value.code == "VERIFICATION_CHAIN_NOT_READY"


def test_prompt_is_fixed_and_contains_no_dynamic_command_surface() -> None:
    assert "README.md" in STATIC_PROMPT
    assert "READY_FOR_REVIEW" in STATIC_PROMPT
    assert "Do not commit" in STATIC_PROMPT
    assert "codex exec" not in STATIC_PROMPT
    assert "|" not in STATIC_PROMPT
    assert "$(" not in STATIC_PROMPT
