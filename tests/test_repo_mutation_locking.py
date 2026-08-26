from pathlib import Path

import pytest

from app.audit.store import SQLiteAuditStore
from app.harness.kernel import (
    AgentLoop,
    AgentLoopRequest,
    ApprovalGate,
    PermissionPolicy,
    ToolInvocationContext,
    ToolSpec,
)
from app.locks.repo_mutation import RepoMutationLockStore
from app.memory.store import compute_repo_key
from app.patching.apply import PatchApplyResult
from app.patching.store import SQLitePatchStore
from app.tools.tool_executor import ToolExecutionResult
from app.worktrees.manager import WorktreeCreateResult


def _write_tool(name: str) -> ToolSpec:
    return ToolSpec(
        name=name,
        description=f"{name} test tool",
        read_only=False,
        risk="write",
        requires_approval=True,
    )


def test_repo_mutation_lock_store_acquire_release_and_conflict(tmp_path: Path) -> None:
    store = RepoMutationLockStore.for_repo(tmp_path)

    first = store.acquire(repo_key="repo_a", operation="patch_apply")
    second = store.acquire(repo_key="repo_a", operation="verification_run")

    assert first.acquired is True
    assert first.owner_token
    assert second.acquired is False
    assert second.reason == "lock_conflict"

    assert store.release(first) is True
    third = store.acquire(repo_key="repo_a", operation="verification_run")

    assert third.acquired is True
    assert third.owner_token != first.owner_token


def test_repo_mutation_lock_store_scopes_by_repo_key(tmp_path: Path) -> None:
    store = RepoMutationLockStore.for_repo(tmp_path)

    first = store.acquire(repo_key="repo_a", operation="patch_apply")
    second = store.acquire(repo_key="repo_b", operation="patch_apply")

    assert first.acquired is True
    assert second.acquired is True


def test_repo_mutation_lock_release_rejects_owner_token_mismatch(tmp_path: Path) -> None:
    store = RepoMutationLockStore.for_repo(tmp_path)
    first = store.acquire(repo_key="repo_a", operation="patch_apply")
    wrong_owner = first.with_owner_token("wrong_owner")

    assert store.release(wrong_owner) is False
    assert store.acquire(repo_key="repo_a", operation="patch_apply").reason == "lock_conflict"


def test_write_tool_permission_requires_acquired_lock_context() -> None:
    policy = PermissionPolicy()
    gate = ApprovalGate()
    context = ToolInvocationContext(
        tool_name="patch_apply",
        user_id="u001",
        repo_key="repo_a",
        intent="patch_apply",
        patch_id="patch_20260627_abcdef",
        confirmed=True,
        patch_status="pending",
        diff_hash_match=True,
        expires_at_valid=True,
        scope_valid=True,
    )

    denied = policy.decide(_write_tool("patch_apply"), tool_name="patch_apply", context=context)

    assert denied.status == "deny"
    assert denied.reason == "repo_mutation_lock_required"

    locked_context = context.with_lock(owner_token="owner_1", operation="patch_apply")
    decision = policy.decide(
        _write_tool("patch_apply"),
        tool_name="patch_apply",
        context=locked_context,
    )

    assert decision.status == "ask"
    assert gate.evaluate(decision, context=locked_context) is True


def test_verification_permission_requires_acquired_lock_context() -> None:
    policy = PermissionPolicy()
    context = ToolInvocationContext(
        tool_name="verification_run",
        user_id="u001",
        repo_key="repo_a",
        intent="verification_run",
        command_label="verify",
        confirmed=True,
        scope_valid=True,
    )

    denied = policy.decide(
        _write_tool("verification_run"),
        tool_name="verification_run",
        context=context,
    )

    assert denied.status == "deny"
    assert denied.reason == "repo_mutation_lock_required"


class ExecutorMustNotMutate:
    def worktree_create(self, repo_path: str, user_id: str, patch_id: str) -> None:
        raise AssertionError("worktree_create must not run under lock conflict")

    def patch_apply(self, repo_path: str, diff_text: str, **kwargs) -> None:
        raise AssertionError("patch_apply must not run under lock conflict")

    def verification_run(self, repo_path: str, command_label: str) -> None:
        raise AssertionError("verification_run must not run under lock conflict")

    def search_repo_rag(self, repo_path: str, keyword: str, search_plan):
        return type(
            "SearchResult",
            (),
            {
                "tool_name": "repo_rag",
                "parameters": {"keyword": keyword},
                "results": [],
                "error": None,
                "audit_summary": {},
                "evidence_pack": None,
                "call_summary": lambda self: {
                    "tool_name": "repo_rag",
                    "keyword": keyword,
                    "status": "success",
                    "result_count": "0",
                },
            },
        )()


class SuccessfulVerificationExecutor:
    def verification_run(self, repo_path: str, command_label: str) -> ToolExecutionResult:
        return ToolExecutionResult(
            tool_name="verification_run",
            parameters={
                "command_label": command_label,
                "exit_code": "0",
                "duration_ms": "1",
                "timed_out": "false",
                "truncated": "false",
            },
            audit_summary={
                "command_label": command_label,
                "status": "success",
                "exit_code": 0,
                "duration_ms": 1,
                "timed_out": "false",
                "truncated": "false",
            },
        )


class ExplodingVerificationExecutor:
    def verification_run(self, repo_path: str, command_label: str) -> ToolExecutionResult:
        raise RuntimeError(f"boom from {repo_path}\\mutation_locks.sqlite3")


class SuccessfulPatchApplyExecutor:
    def worktree_create(
        self,
        repo_path: str,
        user_id: str,
        patch_id: str,
    ) -> ToolExecutionResult:
        return ToolExecutionResult(
            tool_name="worktree_create",
            parameters={"worktree_id": "wt_20260627_abcdef"},
            audit_summary={"status": "ready"},
            worktree_create_result=WorktreeCreateResult(
                created=True,
                status="ready",
                worktree_id="wt_20260627_abcdef",
                execution_repo_path=repo_path,
                base_commit="base_1",
                public_summary="worktree_id=wt_20260627_abcdef; status=ready",
            ),
        )

    def patch_apply(self, repo_path: str, diff_text: str) -> ToolExecutionResult:
        return ToolExecutionResult(
            tool_name="patch_apply",
            parameters={},
            results=[{"file_path": "app.py", "line_number": 0, "line_text": ""}],
            audit_summary={"changed_files": 1},
            patch_apply_result=PatchApplyResult(
                applied=True,
                changed_files=["app.py"],
            ),
        )


class WorktreeManagerMustNotPreflight:
    def prepare_promotion(self, *args, **kwargs) -> None:
        raise AssertionError("promotion preflight must run under acquired lock only")

    def prepare_disposal(self, *args, **kwargs) -> None:
        raise AssertionError("disposal preflight must run under acquired lock only")

    def prepare_reverification(self, *args, **kwargs) -> None:
        raise AssertionError("reverification preflight must run under acquired lock only")


def _request(repo: Path, message: str) -> AgentLoopRequest:
    return AgentLoopRequest(
        message=message,
        repo_path=str(repo),
        trace_id="trace_repo_mutation_lock",
        user_id="u001",
        session_id="s001",
    )


def _create_pending_patch(repo: Path) -> str:
    repo.mkdir(parents=True, exist_ok=True)
    (repo / "app.py").write_text("old\n", encoding="utf-8")
    store = SQLitePatchStore.for_repo(repo)
    patch = store.create_pending_patch(
        user_id="u001",
        repo_key=compute_repo_key(repo),
        target_files=["app.py"],
        diff_text="--- a/app.py\n+++ b/app.py\n@@ -1 +1 @@\n-old\n+new\n",
        summary="test patch",
    )
    return patch.patch_id


def test_patch_apply_refuses_before_worktree_create_when_repo_lock_held(
    tmp_path: Path,
) -> None:
    patch_id = _create_pending_patch(tmp_path)
    RepoMutationLockStore.for_repo(tmp_path).acquire(
        repo_key=compute_repo_key(tmp_path),
        operation="verification_run",
    )

    result = AgentLoop(tool_executor=ExecutorMustNotMutate()).run(
        _request(tmp_path, f"确认 patch {patch_id}")
    )

    assert result.tool_calls == []
    assert "repo_mutation_lock_conflict" in result.answer
    assert any(
        event.event_type == "repo_mutation_lock"
        and "outcome=conflict" in event.summary
        for event in result.trace_events_internal
    )
    audit_store, repo_key = SQLiteAuditStore.for_existing_repo(tmp_path)
    events = audit_store.recent_events(user_id="u001", repo_key=repo_key, limit=10)
    assert any(
        event.event_type == "repo_mutation_lock"
        and event.payload["outcome"] == "conflict"
        and event.payload["operation"] == "patch_apply"
        for event in events
    )


def test_patch_verify_refuses_before_worktree_create_when_repo_lock_held(
    tmp_path: Path,
) -> None:
    patch_id = _create_pending_patch(tmp_path)
    RepoMutationLockStore.for_repo(tmp_path).acquire(
        repo_key=compute_repo_key(tmp_path),
        operation="verification_run",
    )

    result = AgentLoop(tool_executor=ExecutorMustNotMutate()).run(
        _request(tmp_path, f"确认 patch {patch_id} 并运行验证")
    )

    assert result.tool_calls == []
    assert "repo_mutation_lock_conflict" in result.answer
    assert any(
        event.event_type == "repo_mutation_lock"
        and "operation=patch_verify" in event.summary
        and "outcome=conflict" in event.summary
        for event in result.trace_events_internal
    )


def test_verification_refuses_before_executor_when_repo_lock_held(tmp_path: Path) -> None:
    tmp_path.mkdir(parents=True, exist_ok=True)
    RepoMutationLockStore.for_repo(tmp_path).acquire(
        repo_key=compute_repo_key(tmp_path),
        operation="patch_apply",
    )

    result = AgentLoop(tool_executor=ExecutorMustNotMutate()).run(
        _request(tmp_path, "运行验证")
    )

    assert result.tool_calls == []
    assert "repo_mutation_lock_conflict" in result.answer
    assert any(
        event.event_type == "repo_mutation_lock"
        and "operation=verification_run" in event.summary
        and "outcome=conflict" in event.summary
        for event in result.trace_events_internal
    )


def test_lock_store_acquisition_exception_fails_closed_without_storage_details(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tmp_path.mkdir(parents=True, exist_ok=True)

    def fail_for_repo(cls, repo_path):
        raise OSError(f"{tmp_path}\\mutation_locks.sqlite3")

    monkeypatch.setattr(RepoMutationLockStore, "for_repo", classmethod(fail_for_repo))

    result = AgentLoop(tool_executor=ExecutorMustNotMutate()).run(
        _request(tmp_path, "run verification")
    )

    public = f"{result.answer} {result.trace_events_internal}"
    assert result.tool_calls == []
    assert "repo_mutation_lock_conflict" in result.answer
    assert "lock_unavailable" in result.answer
    assert str(tmp_path) not in public
    assert "mutation_locks.sqlite3" not in public
    assert any(
        event.event_type == "repo_mutation_lock"
        and "operation=verification_run" in event.summary
        and "outcome=unavailable" in event.summary
        and "reason=lock_unavailable" in event.summary
        for event in result.trace_events_internal
    )


def test_promotion_refuses_before_preflight_when_repo_lock_held(tmp_path: Path) -> None:
    tmp_path.mkdir(parents=True, exist_ok=True)
    RepoMutationLockStore.for_repo(tmp_path).acquire(
        repo_key=compute_repo_key(tmp_path),
        operation="patch_apply",
    )

    result = AgentLoop(worktree_manager=WorktreeManagerMustNotPreflight()).run(
        _request(tmp_path, "confirm promote worktree wt_20260627_abcdef")
    )

    assert "repo_mutation_lock_conflict" in result.answer
    assert result.tool_calls == []


def test_disposal_refuses_before_preflight_when_repo_lock_held(tmp_path: Path) -> None:
    tmp_path.mkdir(parents=True, exist_ok=True)
    RepoMutationLockStore.for_repo(tmp_path).acquire(
        repo_key=compute_repo_key(tmp_path),
        operation="patch_apply",
    )

    result = AgentLoop(worktree_manager=WorktreeManagerMustNotPreflight()).run(
        _request(tmp_path, "confirm discard worktree wt_20260627_abcdef")
    )

    assert "repo_mutation_lock_conflict" in result.answer
    assert result.tool_calls == []


def test_reverification_refuses_before_preflight_when_repo_lock_held(
    tmp_path: Path,
) -> None:
    tmp_path.mkdir(parents=True, exist_ok=True)
    RepoMutationLockStore.for_repo(tmp_path).acquire(
        repo_key=compute_repo_key(tmp_path),
        operation="patch_apply",
    )

    result = AgentLoop(worktree_manager=WorktreeManagerMustNotPreflight()).run(
        _request(tmp_path, "重新验证 worktree wt_20260627_abcdef verify")
    )

    assert "repo_mutation_lock_conflict" in result.answer
    assert result.tool_calls == []


def test_read_only_worktree_inventory_does_not_acquire_or_block_on_lock(
    tmp_path: Path,
) -> None:
    tmp_path.mkdir(parents=True, exist_ok=True)
    RepoMutationLockStore.for_repo(tmp_path).acquire(
        repo_key=compute_repo_key(tmp_path),
        operation="patch_apply",
    )

    result = AgentLoop().run(_request(tmp_path, "列出 worktree"))

    assert "当前 scope worktrees: 0" in result.answer
    assert "repo_mutation_lock_conflict" not in result.answer
    assert not any(
        event.event_type == "repo_mutation_lock"
        for event in result.trace_events_internal
    )


def test_release_failure_is_reported_without_storage_details(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tmp_path.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(RepoMutationLockStore, "release", lambda self, lock: False)

    result = AgentLoop(tool_executor=SuccessfulVerificationExecutor()).run(
        _request(tmp_path, "运行验证")
    )

    assert "repo_mutation_lock_release_failed" in result.answer
    public = f"{result.answer} {result.trace_events_internal}"
    assert str(tmp_path) not in public
    assert "mutation_locks.sqlite3" not in public
    assert any(
        event.event_type == "repo_mutation_lock"
        and "outcome=release_failed" in event.summary
        for event in result.trace_events_internal
    )


def test_successful_mutation_records_acquired_and_released_lock_events(
    tmp_path: Path,
) -> None:
    tmp_path.mkdir(parents=True, exist_ok=True)

    result = AgentLoop(tool_executor=SuccessfulVerificationExecutor()).run(
        _request(tmp_path, "run verification")
    )

    assert any(
        event.event_type == "repo_mutation_lock"
        and "operation=verification_run" in event.summary
        and "outcome=acquired" in event.summary
        for event in result.trace_events_internal
    )
    assert any(
        event.event_type == "repo_mutation_lock"
        and "operation=verification_run" in event.summary
        and "outcome=released" in event.summary
        for event in result.trace_events_internal
    )

    audit_store, repo_key = SQLiteAuditStore.for_existing_repo(tmp_path)
    events = audit_store.recent_events(user_id="u001", repo_key=repo_key, limit=10)
    outcomes = {
        event.payload["outcome"]
        for event in events
        if event.event_type == "repo_mutation_lock"
    }
    assert {"acquired", "released"}.issubset(outcomes)


def test_verification_runner_exception_releases_lock_without_storage_details(
    tmp_path: Path,
) -> None:
    tmp_path.mkdir(parents=True, exist_ok=True)

    result = AgentLoop(tool_executor=ExplodingVerificationExecutor()).run(
        _request(tmp_path, "run verification")
    )

    public = f"{result.answer} {result.trace_events_internal} {result.tool_calls}"
    assert "runner_error" in public
    assert str(tmp_path) not in public
    assert "mutation_locks.sqlite3" not in public
    assert any(
        event.event_type == "repo_mutation_lock"
        and "operation=verification_run" in event.summary
        and "outcome=released" in event.summary
        for event in result.trace_events_internal
    )

    lock = RepoMutationLockStore.for_repo(tmp_path).acquire(
        repo_key=compute_repo_key(tmp_path),
        operation="patch_apply",
    )
    assert lock.acquired is True


def test_patch_apply_release_failure_is_reported_without_storage_details(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    patch_id = _create_pending_patch(tmp_path)
    monkeypatch.setattr(RepoMutationLockStore, "release", lambda self, lock: False)

    result = AgentLoop(tool_executor=SuccessfulPatchApplyExecutor()).run(
        _request(tmp_path, f"confirm patch {patch_id}")
    )

    assert "repo_mutation_lock_release_failed" in result.answer
    public = f"{result.answer} {result.trace_events_internal}"
    assert str(tmp_path) not in public
    assert "mutation_locks.sqlite3" not in public
    assert any(
        event.event_type == "repo_mutation_lock"
        and "operation=patch_apply" in event.summary
        and "outcome=release_failed" in event.summary
        for event in result.trace_events_internal
    )
