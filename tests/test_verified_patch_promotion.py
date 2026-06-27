from pathlib import Path
import subprocess

import pytest

from app.audit.store import SQLiteAuditStore
from app.harness.kernel import AgentLoop, AgentLoopRequest, PermissionPolicy, ToolRegistry
from app.memory.store import compute_repo_key
from app.patching.apply import PatchApplyResult, apply_unified_diff
from app.patching.store import (
    PATCH_STATUS_APPLIED_IN_WORKTREE,
    PATCH_STATUS_DISCARDED,
    PATCH_STATUS_PROMOTED,
    SQLitePatchStore,
)
from app.patching.types import ToolInvocationContext
from app.tools.tool_executor import ToolExecutionResult, ToolExecutor
from app.worktrees.manager import WorktreeManager
from app.worktrees.promotion import parse_verified_patch_promotion_request
from app.worktrees.store import (
    WORKTREE_STATUS_DISCARDED,
    WORKTREE_STATUS_PROMOTED,
    WORKTREE_STATUS_VERIFICATION_SUCCEEDED,
    SQLiteWorktreeStore,
)


def _git(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
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


def _create_verified_worktree(repo: Path, *, user_id: str = "u001"):
    patch_store = SQLitePatchStore.for_repo(repo)
    repo_key = compute_repo_key(repo)
    patch = patch_store.create_pending_patch(
        user_id=user_id,
        repo_key=repo_key,
        target_files=["app.py"],
        diff_text=(
            "--- a/app.py\n+++ b/app.py\n@@ -1 +1 @@\n-main\n+worktree\n"
        ),
        summary="worktree patch",
    )
    created = WorktreeManager().create(
        repo_path=str(repo), user_id=user_id, patch_id=patch.patch_id
    )
    assert created.created is True
    assert apply_unified_diff(created.execution_repo_path, patch.diff_text).applied is True
    patch_store.mark_status(patch.patch_id, PATCH_STATUS_APPLIED_IN_WORKTREE)
    manager = WorktreeManager()
    manager.record_patch_result(
        repo_path=str(repo),
        user_id=user_id,
        worktree_id=created.worktree_id,
        applied=True,
        changed_files=["app.py"],
    )
    manager.record_verification_result(
        repo_path=str(repo),
        user_id=user_id,
        worktree_id=created.worktree_id,
        command_label="pytest",
        succeeded=True,
    )
    return created, patch_store, patch, repo_key


def _request(repo: Path, message: str, *, user_id: str = "u001") -> AgentLoopRequest:
    return AgentLoopRequest(
        message=message,
        repo_path=str(repo),
        trace_id="trace_verified_patch_promotion",
        user_id=user_id,
        session_id="s001",
    )


@pytest.mark.parametrize(
    "message",
    [
        "confirm promote worktree wt_20260626_abcdef",
        "确认提升 worktree wt_20260626_abcdef",
    ],
)
def test_parser_accepts_only_exact_confirmed_promotion_commands(message: str) -> None:
    parsed = parse_verified_patch_promotion_request(message)

    assert parsed.handled is True
    assert parsed.confirmed is True
    assert parsed.rejected is False
    assert parsed.worktree_id == "wt_20260626_abcdef"


@pytest.mark.parametrize(
    "message",
    [
        "promote worktree wt_20260626_abcdef",
        "confirm promote worktree wt_20260626_abcdef now",
        "confirm promote worktree ../../main",
        "confirm promote worktree wt_20260626_abcdef | more",
        "please confirm promote worktree wt_20260626_abcdef",
    ],
)
def test_parser_rejects_command_like_promotion_requests_as_a_whole(message: str) -> None:
    parsed = parse_verified_patch_promotion_request(message)

    assert parsed.handled is True
    assert parsed.rejected is True


def test_malformed_promotion_does_not_fall_through_to_later_routes(tmp_path: Path) -> None:
    _init_repo(tmp_path)

    result = AgentLoop().run(
        _request(tmp_path, "confirm promote worktree wt_20260626_abcdef | more")
    )

    assert result.tool_calls == []
    assert result.trace_events_internal[0].event_type == "verified_patch_promotion_summarized"
    store, repo_key = SQLiteAuditStore.for_existing_repo(tmp_path)
    events = store.recent_events(user_id="u001", repo_key=repo_key, limit=20)
    event = next(event for event in events if event.event_type == "verified_patch_promotion")
    assert event.payload["confirmation"] == "false"


def test_verified_promotion_applies_stored_patch_and_marks_both_lifecycles(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    created, patch_store, patch, repo_key = _create_verified_worktree(tmp_path)

    result = AgentLoop().run(
        _request(tmp_path, f"confirm promote worktree {created.worktree_id}")
    )

    worktree_store = SQLiteWorktreeStore.for_existing_repo(tmp_path)[0]
    worktree = worktree_store.get_worktree(
        created.worktree_id, user_id="u001", repo_key=repo_key
    )
    stored_patch = patch_store.get_patch(
        patch.patch_id, user_id="u001", repo_key=repo_key
    )
    events = SQLiteAuditStore.for_existing_repo(tmp_path)[0].recent_events(
        user_id="u001", repo_key=repo_key, limit=20
    )

    assert (tmp_path / "app.py").read_text(encoding="utf-8") == "worktree\n"
    assert [call["tool_name"] for call in result.tool_calls] == ["patch_apply"]
    assert worktree is not None and worktree.status == WORKTREE_STATUS_PROMOTED
    assert stored_patch is not None and stored_patch.status == PATCH_STATUS_PROMOTED
    event = next(event for event in events if event.event_type == "verified_patch_promotion")
    assert event.payload["patch_id"] == patch.patch_id
    public = f"{result.answer} {result.tool_calls}"
    assert str(tmp_path) not in public
    assert set(result.to_agent_result()) == {"answer", "related_files", "tool_calls"}


def test_tampered_worktree_content_stops_before_patch_apply(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    created, _, _, _ = _create_verified_worktree(tmp_path)
    (Path(created.execution_repo_path) / "app.py").write_text("tampered\n", encoding="utf-8")

    result = AgentLoop().run(
        _request(tmp_path, f"confirm promote worktree {created.worktree_id}")
    )

    assert result.tool_calls == []
    assert "worktree_content_mismatch" in result.answer
    assert (tmp_path / "app.py").read_text(encoding="utf-8") == "main\n"


def test_dirty_main_workspace_stops_before_patch_apply(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    created, _, _, _ = _create_verified_worktree(tmp_path)
    (tmp_path / "untracked.txt").write_text("dirty\n", encoding="utf-8")

    result = AgentLoop().run(
        _request(tmp_path, f"confirm promote worktree {created.worktree_id}")
    )

    assert result.tool_calls == []
    assert "main_workspace_dirty" in result.answer
    assert (tmp_path / "app.py").read_text(encoding="utf-8") == "main\n"


def test_main_head_drift_stops_before_patch_apply(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    created, _, _, _ = _create_verified_worktree(tmp_path)
    _git("commit", "--allow-empty", "-m", "main drift", cwd=tmp_path)

    result = AgentLoop().run(
        _request(tmp_path, f"confirm promote worktree {created.worktree_id}")
    )

    assert result.tool_calls == []
    assert "main_head_base_mismatch" in result.answer
    assert (tmp_path / "app.py").read_text(encoding="utf-8") == "main\n"


def test_atomic_promotion_rechecks_head_before_write_after_preflight(
    tmp_path: Path,
) -> None:
    _init_repo(tmp_path)
    created, patch_store, patch, repo_key = _create_verified_worktree(tmp_path)

    class DriftingExecutor(ToolExecutor):
        def patch_apply(self, repo_path: str, diff_text: str, **kwargs):
            _git("commit", "--allow-empty", "-m", "clean drift", cwd=Path(repo_path))
            return super().patch_apply(repo_path, diff_text, **kwargs)

    result = AgentLoop(tool_executor=DriftingExecutor()).run(
        _request(tmp_path, f"confirm promote worktree {created.worktree_id}")
    )

    worktree = SQLiteWorktreeStore.for_existing_repo(tmp_path)[0].get_worktree(
        created.worktree_id, user_id="u001", repo_key=repo_key
    )
    stored_patch = patch_store.get_patch(
        patch.patch_id, user_id="u001", repo_key=repo_key
    )
    assert "failed" in result.answer
    assert result.tool_calls[0]["error"] == "atomic_apply_base_mismatch"
    assert (tmp_path / "app.py").read_text(encoding="utf-8") == "main\n"
    assert worktree is not None and worktree.status == WORKTREE_STATUS_VERIFICATION_SUCCEEDED
    assert stored_patch is not None and stored_patch.status == PATCH_STATUS_APPLIED_IN_WORKTREE


def test_cross_scope_promotion_stops_before_patch_apply(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    created, _, _, _ = _create_verified_worktree(tmp_path)

    result = AgentLoop().run(
        _request(
            tmp_path,
            f"confirm promote worktree {created.worktree_id}",
            user_id="u002",
        )
    )

    assert result.tool_calls == []
    assert (tmp_path / "app.py").read_text(encoding="utf-8") == "main\n"


def test_promotion_preflight_does_not_create_a_journal(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    created, _, _, _ = _create_verified_worktree(tmp_path)

    preflight = WorktreeManager().prepare_promotion(
        repo_path=str(tmp_path), user_id="u001", worktree_id=created.worktree_id
    )

    assert preflight.accepted is True
    import sqlite3

    with sqlite3.connect(tmp_path / ".repopilot" / "patches.sqlite3") as conn:
        tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master")}
    assert "patch_promotions" not in tables


def test_staging_failure_does_not_partially_write_main_workspace(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.patching import apply as patch_apply

    (tmp_path / "a.py").write_text("old a\n", encoding="utf-8")
    (tmp_path / "b.py").write_text("old b\n", encoding="utf-8")
    diff = (
        "--- a/a.py\n+++ b/a.py\n@@ -1 +1 @@\n-old a\n+new a\n"
        "--- a/b.py\n+++ b/b.py\n@@ -1 +1 @@\n-old b\n+new b\n"
    )

    def fail_second_stage(target: Path, content: str) -> Path:
        if target.name == "b.py":
            raise OSError("staging failed")
        return target

    monkeypatch.setattr(patch_apply, "_write_staged_file", fail_second_stage)
    result = apply_unified_diff(tmp_path, diff)

    assert result.applied is False
    assert (tmp_path / "a.py").read_text(encoding="utf-8") == "old a\n"
    assert (tmp_path / "b.py").read_text(encoding="utf-8") == "old b\n"


def test_commit_failure_restores_replaced_targets_from_staged_originals(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.patching import apply as patch_apply

    (tmp_path / "a.py").write_text("old a\n", encoding="utf-8")
    (tmp_path / "b.py").write_text("old b\n", encoding="utf-8")
    diff = (
        "--- a/a.py\n+++ b/a.py\n@@ -1 +1 @@\n-old a\n+new a\n"
        "--- a/b.py\n+++ b/b.py\n@@ -1 +1 @@\n-old b\n+new b\n"
    )
    original_replace = patch_apply.os.replace

    def fail_second_commit(source: str | Path, target: str | Path) -> None:
        if Path(target).name == "b.py":
            raise OSError("commit failed")
        original_replace(source, target)

    monkeypatch.setattr(patch_apply.os, "replace", fail_second_commit)
    result = apply_unified_diff(tmp_path, diff)

    assert result.applied is False
    assert result.error == "io_error"
    assert (tmp_path / "a.py").read_text(encoding="utf-8") == "old a\n"
    assert (tmp_path / "b.py").read_text(encoding="utf-8") == "old b\n"


def test_promotion_atomic_patch_apply_uses_git_not_python_file_replacement(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.patching import apply as patch_apply

    _init_repo(tmp_path)
    (tmp_path / "b.py").write_text("old b\n", encoding="utf-8")
    _git("add", "b.py", cwd=tmp_path)
    _git("commit", "-m", "add second file", cwd=tmp_path)
    diff = (
        "--- a/app.py\n+++ b/app.py\n@@ -1 +1 @@\n-main\n+new a\n"
        "--- a/b.py\n+++ b/b.py\n@@ -1 +1 @@\n-old b\n+new b\n"
    )
    monkeypatch.setattr(
        patch_apply.os,
        "replace",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("not used")),
    )

    result = ToolExecutor().patch_apply(str(tmp_path), diff, require_atomic=True)

    assert result.patch_apply_result is not None and result.patch_apply_result.applied
    assert (tmp_path / "app.py").read_text(encoding="utf-8") == "new a\n"
    assert (tmp_path / "b.py").read_text(encoding="utf-8") == "new b\n"


def test_atomic_patch_apply_rechecks_clean_workspace_before_write(tmp_path: Path) -> None:
    from app.patching.apply import apply_unified_diff_atomically

    _init_repo(tmp_path)
    (tmp_path / "untracked.txt").write_text("dirty\n", encoding="utf-8")
    diff = "--- a/app.py\n+++ b/app.py\n@@ -1 +1 @@\n-main\n+new\n"

    result = apply_unified_diff_atomically(tmp_path, diff)

    assert result.applied is False
    assert result.error == "main_workspace_dirty"
    assert (tmp_path / "app.py").read_text(encoding="utf-8") == "main\n"


def test_atomic_patch_apply_rechecks_expected_base_before_write(tmp_path: Path) -> None:
    from app.patching.apply import apply_unified_diff_atomically

    _init_repo(tmp_path)
    base = _git("rev-parse", "HEAD", cwd=tmp_path).stdout.strip()
    _git("commit", "--allow-empty", "-m", "clean drift", cwd=tmp_path)
    diff = "--- a/app.py\n+++ b/app.py\n@@ -1 +1 @@\n-main\n+new\n"

    result = apply_unified_diff_atomically(
        tmp_path,
        diff,
        expected_base_commit=base,
    )

    assert result.applied is False
    assert result.error == "atomic_apply_base_mismatch"
    assert (tmp_path / "app.py").read_text(encoding="utf-8") == "main\n"


def test_permission_policy_accepts_only_fully_preflighted_promotion_context() -> None:
    policy = PermissionPolicy()
    tool = ToolRegistry.with_default_tools().get("patch_apply")
    ordinary = ToolInvocationContext(
        tool_name="patch_apply",
        intent="patch_apply",
        confirmed=True,
        patch_status=PATCH_STATUS_APPLIED_IN_WORKTREE,
        diff_hash_match=True,
        expires_at_valid=True,
        scope_valid=True,
    )
    promotion = ToolInvocationContext(
        tool_name="patch_apply",
        intent="patch_promotion_apply",
        confirmed=True,
        patch_status=PATCH_STATUS_APPLIED_IN_WORKTREE,
        diff_hash_match=True,
        expires_at_valid=True,
        scope_valid=True,
        promotion_preflight_valid=True,
    )

    assert policy.decide(tool, context=ordinary).status == "deny"
    assert policy.decide(tool, context=promotion).status == "ask"


def test_atomic_state_finalization_failure_rolls_back_main_workspace_and_keeps_lifecycles(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _init_repo(tmp_path)
    created, patch_store, patch, repo_key = _create_verified_worktree(tmp_path)
    monkeypatch.setattr(SQLitePatchStore, "finalize_promotion", lambda *args, **kwargs: False)

    result = AgentLoop().run(
        _request(tmp_path, f"confirm promote worktree {created.worktree_id}")
    )

    worktree = SQLiteWorktreeStore.for_existing_repo(tmp_path)[0].get_worktree(
        created.worktree_id, user_id="u001", repo_key=repo_key
    )
    stored_patch = patch_store.get_patch(
        patch.patch_id, user_id="u001", repo_key=repo_key
    )
    assert "failed" in result.answer
    assert (tmp_path / "app.py").read_text(encoding="utf-8") == "main\n"
    assert worktree is not None and worktree.status == WORKTREE_STATUS_VERIFICATION_SUCCEEDED
    assert stored_patch is not None and stored_patch.status == PATCH_STATUS_APPLIED_IN_WORKTREE
    assert patch_store.promotion_state(
        patch_id=patch.patch_id,
        worktree_id=created.worktree_id,
        user_id="u001",
        repo_key=repo_key,
    ) == "apply_failed"


def test_main_applied_journal_failure_rolls_back_all_promotion_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _init_repo(tmp_path)
    created, patch_store, patch, repo_key = _create_verified_worktree(tmp_path)
    original_update = SQLitePatchStore.update_promotion_state

    def fail_main_applied_state(self, *args, **kwargs):
        if kwargs["state"] == "main_applied":
            return False
        return original_update(self, *args, **kwargs)

    monkeypatch.setattr(SQLitePatchStore, "update_promotion_state", fail_main_applied_state)
    result = AgentLoop().run(
        _request(tmp_path, f"confirm promote worktree {created.worktree_id}")
    )

    worktree = SQLiteWorktreeStore.for_existing_repo(tmp_path)[0].get_worktree(
        created.worktree_id, user_id="u001", repo_key=repo_key
    )
    stored_patch = patch_store.get_patch(
        patch.patch_id, user_id="u001", repo_key=repo_key
    )
    assert "failed" in result.answer
    assert (tmp_path / "app.py").read_text(encoding="utf-8") == "main\n"
    assert worktree is not None and worktree.status == WORKTREE_STATUS_VERIFICATION_SUCCEEDED
    assert stored_patch is not None and stored_patch.status == PATCH_STATUS_APPLIED_IN_WORKTREE
    assert patch_store.promotion_state(
        patch_id=patch.patch_id,
        worktree_id=created.worktree_id,
        user_id="u001",
        repo_key=repo_key,
    ) == "apply_failed"


def test_promotion_finalization_rejects_lifecycle_drift_after_apply(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _init_repo(tmp_path)
    created, patch_store, patch, repo_key = _create_verified_worktree(tmp_path)
    original_update = SQLitePatchStore.update_promotion_state
    worktree_store = SQLiteWorktreeStore.for_existing_repo(tmp_path)[0]

    def drift_worktree_after_main_applied(self, *args, **kwargs):
        updated = original_update(self, *args, **kwargs)
        if updated and kwargs["state"] == "main_applied":
            worktree_store.update_worktree(
                created.worktree_id,
                user_id="u001",
                repo_key=repo_key,
                status=WORKTREE_STATUS_DISCARDED,
            )
        return updated

    monkeypatch.setattr(
        SQLitePatchStore, "update_promotion_state", drift_worktree_after_main_applied
    )
    result = AgentLoop().run(
        _request(tmp_path, f"confirm promote worktree {created.worktree_id}")
    )

    worktree = worktree_store.get_worktree(
        created.worktree_id, user_id="u001", repo_key=repo_key
    )
    stored_patch = patch_store.get_patch(
        patch.patch_id, user_id="u001", repo_key=repo_key
    )
    assert "failed" in result.answer
    assert (tmp_path / "app.py").read_text(encoding="utf-8") == "main\n"
    assert worktree is not None and worktree.status == WORKTREE_STATUS_DISCARDED
    assert stored_patch is not None and stored_patch.status == PATCH_STATUS_APPLIED_IN_WORKTREE
    assert patch_store.promotion_state(
        patch_id=patch.patch_id,
        worktree_id=created.worktree_id,
        user_id="u001",
        repo_key=repo_key,
    ) == "apply_failed"


def test_promotion_finalization_rejects_patch_status_drift_after_apply(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _init_repo(tmp_path)
    created, patch_store, patch, repo_key = _create_verified_worktree(tmp_path)
    original_update = SQLitePatchStore.update_promotion_state

    def drift_patch_after_main_applied(self, *args, **kwargs):
        updated = original_update(self, *args, **kwargs)
        if updated and kwargs["state"] == "main_applied":
            patch_store.mark_status_scoped(
                patch.patch_id,
                user_id="u001",
                repo_key=repo_key,
                status=PATCH_STATUS_DISCARDED,
            )
        return updated

    monkeypatch.setattr(
        SQLitePatchStore, "update_promotion_state", drift_patch_after_main_applied
    )
    result = AgentLoop().run(
        _request(tmp_path, f"confirm promote worktree {created.worktree_id}")
    )

    worktree = SQLiteWorktreeStore.for_existing_repo(tmp_path)[0].get_worktree(
        created.worktree_id, user_id="u001", repo_key=repo_key
    )
    stored_patch = patch_store.get_patch(
        patch.patch_id, user_id="u001", repo_key=repo_key
    )
    assert "failed" in result.answer
    assert (tmp_path / "app.py").read_text(encoding="utf-8") == "main\n"
    assert worktree is not None and worktree.status == WORKTREE_STATUS_VERIFICATION_SUCCEEDED
    assert stored_patch is not None and stored_patch.status == PATCH_STATUS_DISCARDED
    assert patch_store.promotion_state(
        patch_id=patch.patch_id,
        worktree_id=created.worktree_id,
        user_id="u001",
        repo_key=repo_key,
    ) == "apply_failed"


def test_patch_apply_failure_records_retriable_journal_state(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    created, patch_store, patch, repo_key = _create_verified_worktree(tmp_path)

    class FailingExecutor:
        def patch_apply(self, *args, **kwargs):
            return ToolExecutionResult(
                tool_name="patch_apply",
                parameters={},
                error="atomic_apply_failed",
                patch_apply_result=PatchApplyResult(
                    applied=False, error="atomic_apply_failed"
                ),
            )

    result = AgentLoop(tool_executor=FailingExecutor()).run(
        _request(tmp_path, f"confirm promote worktree {created.worktree_id}")
    )

    assert "failed" in result.answer
    assert patch_store.promotion_state(
        patch_id=patch.patch_id,
        worktree_id=created.worktree_id,
        user_id="u001",
        repo_key=repo_key,
    ) == "apply_failed"


def test_preflight_known_promotion_failure_audit_includes_safe_patch_id(
    tmp_path: Path,
) -> None:
    _init_repo(tmp_path)
    created, _, patch, repo_key = _create_verified_worktree(tmp_path)

    class DenyingApprovalGate:
        def evaluate(self, *args, **kwargs) -> bool:
            return False

    result = AgentLoop(approval_gate=DenyingApprovalGate()).run(
        _request(tmp_path, f"confirm promote worktree {created.worktree_id}")
    )

    events = SQLiteAuditStore.for_existing_repo(tmp_path)[0].recent_events(
        user_id="u001", repo_key=repo_key, limit=20
    )
    event = next(event for event in events if event.event_type == "verified_patch_promotion")
    assert "failed" in result.answer
    assert event.payload["patch_id"] == patch.patch_id
    assert str(tmp_path) not in f"{event.summary} {event.payload}"


def test_promoted_worktree_is_terminal_for_v25_mutation_routes(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    created, _, _, _ = _create_verified_worktree(tmp_path)
    loop = AgentLoop()
    assert "succeeded" in loop.run(
        _request(tmp_path, f"confirm promote worktree {created.worktree_id}")
    ).answer

    repeated = loop.run(_request(tmp_path, f"confirm promote worktree {created.worktree_id}"))
    reverification = loop.run(
        _request(tmp_path, f"worktree verify {created.worktree_id} verify")
    )
    disposal = loop.run(
        _request(tmp_path, f"confirm discard worktree {created.worktree_id}")
    )

    assert repeated.tool_calls == [] and "failed" in repeated.answer
    assert reverification.tool_calls == [] and "preflight_failed" in reverification.answer
    assert disposal.tool_calls == [] and "failed" in disposal.answer
    assert Path(created.execution_repo_path).exists()
