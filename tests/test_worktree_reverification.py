import shutil
import subprocess
from pathlib import Path

import pytest

from app.audit.store import SQLiteAuditStore
from app.harness.kernel import AgentLoop, AgentLoopRequest, ApprovalGate, ToolRegistry
from app.memory.store import compute_repo_key
from app.patching.store import PATCH_STATUS_APPLIED_IN_WORKTREE, SQLitePatchStore
from app.tools.tool_executor import ToolExecutionResult
from app.worktrees.manager import WorktreeManager
from app.worktrees.reverification import parse_worktree_reverification_request
from app.worktrees.store import (
    WORKTREE_STATUS_CREATE_FAILED,
    WORKTREE_STATUS_PATCH_APPLIED,
    WORKTREE_STATUS_PATCH_FAILED,
    WORKTREE_STATUS_READY,
    WORKTREE_STATUS_VERIFICATION_FAILED,
    WORKTREE_STATUS_VERIFICATION_SUCCEEDED,
    SQLiteWorktreeStore,
)


def _git(*args: str, cwd: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=check,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def _init_repo(repo: Path) -> None:
    repo.mkdir(parents=True, exist_ok=True)
    _git("init", "-b", "main", cwd=repo)
    _git("config", "user.email", "test@example.com", cwd=repo)
    _git("config", "user.name", "RepoPilot Test", cwd=repo)
    (repo / ".gitignore").write_text(".repopilot/\n", encoding="utf-8")
    (repo / "app.py").write_text("main\n", encoding="utf-8")
    _git("add", ".", cwd=repo)
    _git("commit", "-m", "init", cwd=repo)


def _create_applied_worktree(repo: Path, *, user_id: str = "u001"):
    patch_store = SQLitePatchStore.for_repo(repo)
    repo_key = compute_repo_key(repo)
    patch = patch_store.create_pending_patch(
        user_id=user_id,
        repo_key=repo_key,
        target_files=["app.py"],
        diff_text="--- a/app.py\n+++ b/app.py\n@@ -1 +1 @@\n-main\n+worktree\n",
        summary="worktree patch",
    )
    created = WorktreeManager().create(
        repo_path=str(repo),
        user_id=user_id,
        patch_id=patch.patch_id,
    )
    patch_store.mark_status(patch.patch_id, PATCH_STATUS_APPLIED_IN_WORKTREE)
    WorktreeManager().record_patch_result(
        repo_path=str(repo),
        user_id=user_id,
        worktree_id=created.worktree_id,
        applied=True,
        changed_files=["app.py"],
    )
    return created, patch_store, patch, repo_key


class RecordingVerificationExecutor:
    def __init__(self, *, status: str = "success") -> None:
        self.status = status
        self.calls: list[tuple[str, str]] = []

    def verification_run(self, repo_path: str, command_label: str) -> ToolExecutionResult:
        self.calls.append((repo_path, command_label))
        exit_code = 0 if self.status == "success" else 1
        return ToolExecutionResult(
            tool_name="verification_run",
            parameters={
                "command_label": command_label,
                "exit_code": str(exit_code),
                "duration_ms": "7",
                "timed_out": "false",
                "truncated": "false",
            },
            audit_summary={
                "command_label": command_label,
                "status": self.status,
                "exit_code": exit_code,
                "duration_ms": 7,
                "timed_out": "false",
                "truncated": "false",
                "stdout_excerpt": "C:/Users/person/repo API_KEY=secret",
                "stderr_excerpt": ".repopilot/audit.sqlite3",
            },
        )


class ForbiddenExecutor:
    def __getattr__(self, name: str):
        raise AssertionError(f"unexpected tool call: {name}")


class RaisingVerificationExecutor:
    def verification_run(self, repo_path: str, command_label: str) -> ToolExecutionResult:
        raise OSError("private runner failure")


class RejectingApprovalGate(ApprovalGate):
    def evaluate(self, decision, context=None) -> bool:
        return False


def _request(repo: Path, message: str, *, user_id: str = "u001", trace: str = "trace_v22"):
    return AgentLoopRequest(
        message=message,
        repo_path=str(repo),
        trace_id=trace,
        user_id=user_id,
        session_id="s001",
    )


def test_parser_accepts_exact_english_and_chinese_commands() -> None:
    english = parse_worktree_reverification_request(
        "worktree verify wt_20260614_abcdef pytest"
    )
    chinese = parse_worktree_reverification_request(
        "重新验证 worktree wt_20260614_abcdef verify"
    )

    assert english.handled is True
    assert english.rejected is False
    assert english.worktree_id == "wt_20260614_abcdef"
    assert english.command_label == "pytest"
    assert chinese.command_label == "verify"


@pytest.mark.parametrize(
    "message",
    [
        "worktree verify wt_20260614_abcdef pytest -k one",
        "worktree verify wt_20260614_abcdef ./script.py",
        "worktree verify wt_20260614_abcdef TOKEN=secret",
        "worktree verify wt_20260614_abcdef verify | more",
        "worktree verify wt_20260614_abcdef verify > out.txt",
        "worktree verify wt_20260614_abcdef unknown",
        "please worktree verify wt_20260614_abcdef verify",
    ],
)
def test_parser_rejects_unsafe_or_partial_reverification_without_fallthrough(
    message: str,
) -> None:
    parsed = parse_worktree_reverification_request(message)

    assert parsed.handled is True
    assert parsed.rejected is True


def test_partial_reverification_preserves_safe_worktree_id_for_attempt_audit() -> None:
    parsed = parse_worktree_reverification_request(
        "please worktree verify wt_20260614_abcdef verify"
    )

    assert parsed.rejected is True
    assert parsed.worktree_id == "wt_20260614_abcdef"


def test_unknown_and_cross_scope_ids_stop_before_git_or_verification(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _init_repo(tmp_path)
    created, _, _, _ = _create_applied_worktree(tmp_path)

    def fail_preflight_git(*args, **kwargs):
        raise AssertionError("Git preflight must not run for unknown/cross-scope ids")

    monkeypatch.setattr("app.worktrees.reverification._bounded_git_text", fail_preflight_git)
    loop = AgentLoop(tool_executor=ForbiddenExecutor())

    unknown = loop.run(_request(tmp_path, "worktree verify wt_20260614_unknown verify"))
    cross_user = loop.run(
        _request(
            tmp_path,
            f"worktree verify {created.worktree_id} verify",
            user_id="u002",
            trace="trace_cross_user",
        )
    )

    assert "preflight_failed" in unknown.answer
    assert "preflight_failed" in cross_user.answer
    assert unknown.tool_calls == []
    assert cross_user.tool_calls == []


def test_cross_repo_id_stops_before_git_or_verification(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first_repo = tmp_path / "first"
    second_repo = tmp_path / "second"
    _init_repo(first_repo)
    _init_repo(second_repo)
    created, _, _, _ = _create_applied_worktree(first_repo)

    def fail_preflight_git(*args, **kwargs):
        raise AssertionError("Git preflight must not run for a cross-repo id")

    monkeypatch.setattr("app.worktrees.reverification._bounded_git_text", fail_preflight_git)
    result = AgentLoop(tool_executor=ForbiddenExecutor()).run(
        _request(second_repo, f"worktree verify {created.worktree_id} verify")
    )

    assert "preflight_failed" in result.answer
    assert result.tool_calls == []


@pytest.mark.parametrize("mismatch", ["directory", "registry", "head"])
def test_consistency_mismatch_fails_closed_and_preserves_lifecycle(
    tmp_path: Path,
    mismatch: str,
) -> None:
    _init_repo(tmp_path)
    created, patch_store, patch, repo_key = _create_applied_worktree(tmp_path)
    worktree = Path(created.execution_repo_path)
    if mismatch == "directory":
        shutil.rmtree(worktree)
    elif mismatch == "registry":
        _git("worktree", "remove", "--force", "--force", str(worktree), cwd=tmp_path)
        worktree.mkdir(parents=True)
    else:
        (worktree / "app.py").write_text("new commit\n", encoding="utf-8")
        _git("add", "app.py", cwd=worktree)
        _git("commit", "-m", "move head", cwd=worktree)
    executor = RecordingVerificationExecutor()

    result = AgentLoop(tool_executor=executor).run(
        _request(tmp_path, f"worktree verify {created.worktree_id} verify")
    )

    record = WorktreeManager().get_status(
        repo_path=str(tmp_path), user_id="u001", worktree_id=created.worktree_id
    )
    stored_patch = patch_store.get_patch(patch.patch_id, user_id="u001", repo_key=repo_key)
    assert "preflight_failed" in result.answer
    assert executor.calls == []
    assert record is not None and record.status == WORKTREE_STATUS_PATCH_APPLIED
    assert stored_patch is not None and stored_patch.status == PATCH_STATUS_APPLIED_IN_WORKTREE


def test_registry_path_mismatch_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _init_repo(tmp_path)
    created, _, _, _ = _create_applied_worktree(tmp_path)
    monkeypatch.setattr(
        "app.worktrees.reverification._registry_paths",
        lambda repo_root: {(tmp_path / "different-worktree").resolve().as_posix()},
    )

    result = AgentLoop(tool_executor=ForbiddenExecutor()).run(
        _request(tmp_path, f"worktree verify {created.worktree_id} verify")
    )

    assert "preflight_failed" in result.answer
    assert result.tool_calls == []


@pytest.mark.parametrize(
    "ineligible_status",
    [
        WORKTREE_STATUS_READY,
        WORKTREE_STATUS_CREATE_FAILED,
        WORKTREE_STATUS_PATCH_FAILED,
    ],
)
def test_ineligible_lifecycle_fails_closed_before_git(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    ineligible_status: str,
) -> None:
    _init_repo(tmp_path)
    created, _, _, repo_key = _create_applied_worktree(tmp_path)
    store, _ = SQLiteWorktreeStore.for_existing_repo(tmp_path)
    store.update_worktree(
        created.worktree_id,
        user_id="u001",
        repo_key=repo_key,
        status=ineligible_status,
    )

    def fail_preflight_git(*args, **kwargs):
        raise AssertionError("Git preflight must not run for an ineligible lifecycle")

    monkeypatch.setattr("app.worktrees.reverification._bounded_git_text", fail_preflight_git)
    result = AgentLoop(tool_executor=ForbiddenExecutor()).run(
        _request(tmp_path, f"worktree verify {created.worktree_id} verify")
    )
    record = WorktreeManager().get_status(
        repo_path=str(tmp_path), user_id="u001", worktree_id=created.worktree_id
    )

    assert "preflight_failed" in result.answer
    assert result.tool_calls == []
    assert record is not None and record.status == ineligible_status


@pytest.mark.parametrize("git_behavior", ["malformed", "exception"])
def test_git_preflight_failure_does_not_retry_or_run_verification(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    git_behavior: str,
) -> None:
    _init_repo(tmp_path)
    created, _, _, _ = _create_applied_worktree(tmp_path)
    calls = 0

    def fail_git(*args, **kwargs):
        nonlocal calls
        calls += 1
        if git_behavior == "exception":
            raise OSError("private git failure")
        return "malformed registry output"

    monkeypatch.setattr("app.worktrees.reverification._bounded_git_text", fail_git)
    result = AgentLoop(tool_executor=ForbiddenExecutor()).run(
        _request(tmp_path, f"worktree verify {created.worktree_id} verify")
    )

    assert "preflight_failed" in result.answer
    assert result.tool_calls == []
    assert calls == 1


def test_malformed_registry_with_expected_path_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _init_repo(tmp_path)
    created, _, _, _ = _create_applied_worktree(tmp_path)
    expected = Path(created.execution_repo_path).resolve().as_posix()
    calls = 0

    def malformed_registry(*args, **kwargs):
        nonlocal calls
        calls += 1
        return f"worktree {expected}\0HEAD {'a' * 40}\0detached\0malformed-field\0"

    monkeypatch.setattr(
        "app.worktrees.reverification._bounded_git_text",
        malformed_registry,
    )
    result = AgentLoop(tool_executor=ForbiddenExecutor()).run(
        _request(tmp_path, f"worktree verify {created.worktree_id} verify")
    )

    assert "preflight_failed" in result.answer
    assert result.tool_calls == []
    assert calls == 1


@pytest.mark.parametrize(
    "loop_kwargs",
    [
        {"tool_registry": ToolRegistry()},
        {"approval_gate": RejectingApprovalGate()},
    ],
)
def test_permission_or_approval_failure_preserves_lifecycle(
    tmp_path: Path,
    loop_kwargs: dict,
) -> None:
    _init_repo(tmp_path)
    created, _, _, _ = _create_applied_worktree(tmp_path)

    result = AgentLoop(tool_executor=ForbiddenExecutor(), **loop_kwargs).run(
        _request(tmp_path, f"worktree verify {created.worktree_id} verify")
    )
    record = WorktreeManager().get_status(
        repo_path=str(tmp_path), user_id="u001", worktree_id=created.worktree_id
    )

    assert result.tool_calls == []
    assert record is not None and record.status == WORKTREE_STATUS_PATCH_APPLIED


@pytest.mark.parametrize(
    ("verification_status", "expected_lifecycle"),
    [
        ("success", WORKTREE_STATUS_VERIFICATION_SUCCEEDED),
        ("failed", WORKTREE_STATUS_VERIFICATION_FAILED),
        ("timed_out", WORKTREE_STATUS_VERIFICATION_FAILED),
        ("unavailable", WORKTREE_STATUS_VERIFICATION_FAILED),
    ],
)
def test_reverification_runs_only_in_worktree_updates_lifecycle_and_not_patch(
    tmp_path: Path,
    verification_status: str,
    expected_lifecycle: str,
) -> None:
    _init_repo(tmp_path)
    created, patch_store, patch, repo_key = _create_applied_worktree(tmp_path)
    executor = RecordingVerificationExecutor(status=verification_status)

    result = AgentLoop(tool_executor=executor).run(
        _request(tmp_path, f"worktree verify {created.worktree_id} ruff")
    )

    record = WorktreeManager().get_status(
        repo_path=str(tmp_path), user_id="u001", worktree_id=created.worktree_id
    )
    stored_patch = patch_store.get_patch(patch.patch_id, user_id="u001", repo_key=repo_key)
    assert executor.calls == [(created.execution_repo_path, "ruff")]
    assert (tmp_path / "app.py").read_text(encoding="utf-8") == "main\n"
    assert record is not None and record.status == expected_lifecycle
    assert stored_patch is not None and stored_patch.status == PATCH_STATUS_APPLIED_IN_WORKTREE
    assert result.related_files == []
    assert result.tool_calls[0]["tool_name"] == "verification_run"
    assert f"worktree_id={created.worktree_id}" in result.answer
    assert "command=ruff" in result.answer


def test_verification_failed_lifecycle_can_be_reverified(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    created, _, _, repo_key = _create_applied_worktree(tmp_path)
    store, _ = SQLiteWorktreeStore.for_existing_repo(tmp_path)
    store.update_worktree(
        created.worktree_id,
        user_id="u001",
        repo_key=repo_key,
        status=WORKTREE_STATUS_VERIFICATION_FAILED,
    )
    executor = RecordingVerificationExecutor()

    result = AgentLoop(tool_executor=executor).run(
        _request(tmp_path, f"worktree verify {created.worktree_id} verify")
    )

    assert executor.calls == [(created.execution_repo_path, "verify")]
    assert result.tool_calls[0]["tool_name"] == "verification_run"


def test_runner_exception_sets_failed_lifecycle_without_exposing_exception(
    tmp_path: Path,
) -> None:
    _init_repo(tmp_path)
    created, _, _, _ = _create_applied_worktree(tmp_path)

    result = AgentLoop(tool_executor=RaisingVerificationExecutor()).run(
        _request(tmp_path, f"worktree verify {created.worktree_id} verify")
    )
    record = WorktreeManager().get_status(
        repo_path=str(tmp_path), user_id="u001", worktree_id=created.worktree_id
    )

    assert record is not None and record.status == WORKTREE_STATUS_VERIFICATION_FAILED
    assert "private runner failure" not in result.answer
    assert result.tool_calls[0]["error"] == "runner_error"


def test_each_attempt_persists_redacted_related_audit_and_contract_is_stable(
    tmp_path: Path,
) -> None:
    _init_repo(tmp_path)
    created, _, _, repo_key = _create_applied_worktree(tmp_path)
    executor = RecordingVerificationExecutor()
    loop = AgentLoop(tool_executor=executor)

    first = loop.run(_request(tmp_path, f"worktree verify {created.worktree_id} verify"))
    second = loop.run(
        _request(
            tmp_path,
            f"worktree verify {created.worktree_id} verify",
            trace="trace_v22_second",
        )
    )

    store, _ = SQLiteAuditStore.for_existing_repo(tmp_path)
    events = store.recent_events(user_id="u001", repo_key=repo_key, limit=20)
    reruns = [
        event
        for event in events
        if event.event_type == "verification_result"
        and event.related_id == created.worktree_id
        and event.payload.get("attempt_kind") == "worktree_reverification"
    ]
    stored_text = " ".join(f"{event.summary} {event.payload}" for event in reruns)
    public_text = " ".join(
        [
            first.answer,
            str(first.tool_calls),
            str(first.trace_events_internal),
            second.answer,
            str(second.tool_calls),
            str(second.trace_events_internal),
        ]
    )
    assert len(reruns) == 2
    assert all(event.payload["execution_attempted"] == "true" for event in reruns)
    for sensitive in ("API_KEY=secret", "C:/Users/person", "audit.sqlite3"):
        assert sensitive not in stored_text
        assert sensitive not in public_text
    assert set(first.to_agent_result()) == {"answer", "related_files", "tool_calls"}
    assert set(second.to_agent_result()) == {"answer", "related_files", "tool_calls"}


def test_rejected_partial_attempt_is_related_and_not_executed(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    created, _, _, repo_key = _create_applied_worktree(tmp_path)

    result = AgentLoop(tool_executor=ForbiddenExecutor()).run(
        _request(
            tmp_path,
            f"please worktree verify {created.worktree_id} verify",
            trace="trace_v22_rejected_partial",
        )
    )

    store, _ = SQLiteAuditStore.for_existing_repo(tmp_path)
    events = store.recent_events(user_id="u001", repo_key=repo_key, limit=20)
    attempts = [
        event
        for event in events
        if event.event_type == "verification_result"
        and event.related_id == created.worktree_id
        and event.payload.get("attempt_kind") == "worktree_reverification"
    ]
    assert result.tool_calls == []
    assert len(attempts) == 1
    assert attempts[0].payload["execution_attempted"] == "false"
