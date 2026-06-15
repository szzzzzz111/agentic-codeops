from pathlib import Path
import subprocess

import pytest

from app.memory.store import compute_repo_key
from app.audit.store import SQLiteAuditStore
from app.harness.kernel import AgentLoop, AgentLoopRequest
from app.patching.store import (
    PATCH_STATUS_APPLIED_IN_WORKTREE,
    PATCH_STATUS_DISCARDED,
    SQLitePatchStore,
)
from app.worktrees.disposal import parse_worktree_disposal_request
from app.worktrees.git_metadata import run_git_metadata
from app.worktrees.manager import WorktreeManager
from app.worktrees.store import (
    WORKTREE_STATUS_DISCARDED,
    WORKTREE_STATUS_DISPOSAL_FAILED,
    WORKTREE_STATUS_READY,
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


def _create_retained_worktree(repo: Path, user_id: str = "u001"):
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


@pytest.mark.parametrize(
    ("message", "kind"),
    [
        ("confirm discard worktree wt_20260615_abcdef", "discard"),
        ("确认丢弃 worktree wt_20260615_abcdef", "discard"),
        ("confirm reconcile worktree wt_20260615_abcdef", "reconcile"),
        ("确认协调 worktree wt_20260615_abcdef", "reconcile"),
    ],
)
def test_parser_accepts_only_exact_confirmed_commands(message: str, kind: str) -> None:
    parsed = parse_worktree_disposal_request(message)

    assert parsed.handled is True
    assert parsed.rejected is False
    assert parsed.confirmed is True
    assert parsed.attempt_kind == kind
    assert parsed.worktree_id == "wt_20260615_abcdef"


@pytest.mark.parametrize(
    "message",
    [
        "discard worktree wt_20260615_abcdef",
        "reconcile worktree wt_20260615_abcdef",
        "confirm discard worktree wt_20260615_abcdef now",
        "confirm discard worktree ../../main",
        "confirm discard worktree wt_20260615_abcdef | more",
    ],
)
def test_parser_rejects_command_like_requests_as_a_whole(message: str) -> None:
    parsed = parse_worktree_disposal_request(message)

    assert parsed.handled is True
    assert parsed.rejected is True


@pytest.mark.parametrize(
    "message",
    ["how to discard changes", "how to discard worktree changes", "explain reconciliation"],
)
def test_parser_does_not_match_discussion(message: str) -> None:
    assert parse_worktree_disposal_request(message).handled is False


def test_patch_store_existing_lookup_does_not_create_state(tmp_path: Path) -> None:
    assert SQLitePatchStore.for_existing_repo(tmp_path) is None
    assert not (tmp_path / ".repopilot").exists()


def test_patch_store_scoped_status_update_preserves_other_scope(tmp_path: Path) -> None:
    store = SQLitePatchStore.for_repo(tmp_path)
    patch = store.create_pending_patch(
        user_id="u001",
        repo_key="repo_a",
        target_files=["app.py"],
        diff_text="--- a/app.py\n+++ b/app.py\n",
        summary="patch",
    )

    assert (
        store.mark_status_scoped(
            patch.patch_id,
            user_id="u002",
            repo_key="repo_a",
            status=PATCH_STATUS_DISCARDED,
        )
        is False
    )
    assert (
        store.mark_status_scoped(
            patch.patch_id,
            user_id="u001",
            repo_key="repo_a",
            status=PATCH_STATUS_DISCARDED,
        )
        is True
    )
    assert (
        store.get_patch(patch.patch_id, user_id="u001", repo_key="repo_a").status
        == PATCH_STATUS_DISCARDED
    )


def test_manager_disposes_retained_worktree_in_terminal_order(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    created, patch_store, patch, repo_key = _create_retained_worktree(tmp_path)

    result = WorktreeManager().dispose(
        repo_path=str(tmp_path),
        user_id="u001",
        worktree_id=created.worktree_id,
        attempt_kind="discard",
    )

    stored_worktree = SQLiteWorktreeStore.for_existing_repo(tmp_path)[0].get_worktree(
        created.worktree_id,
        user_id="u001",
        repo_key=repo_key,
    )
    stored_patch = patch_store.get_patch(
        patch.patch_id,
        user_id="u001",
        repo_key=repo_key,
    )
    assert result.succeeded is True
    assert result.completed_step == "patch_discarded"
    assert not Path(created.execution_repo_path).exists()
    assert stored_worktree is not None and stored_worktree.status == WORKTREE_STATUS_DISCARDED
    assert stored_patch is not None and stored_patch.status == PATCH_STATUS_DISCARDED


def test_repeat_disposal_is_idempotent(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    created, _, _, _ = _create_retained_worktree(tmp_path)
    manager = WorktreeManager()
    assert manager.dispose(
        repo_path=str(tmp_path),
        user_id="u001",
        worktree_id=created.worktree_id,
        attempt_kind="discard",
    ).succeeded

    repeated = manager.dispose(
        repo_path=str(tmp_path),
        user_id="u001",
        worktree_id=created.worktree_id,
        attempt_kind="discard",
    )

    assert repeated.succeeded is True
    assert repeated.idempotent is True


def test_reconcile_directory_missing_removes_locked_registry_entry(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    created, _, _, _ = _create_retained_worktree(tmp_path)
    worktree = Path(created.execution_repo_path)
    for child in sorted(worktree.rglob("*"), reverse=True):
        if child.is_file():
            child.unlink()
        elif child.is_dir():
            child.rmdir()
    worktree.rmdir()

    result = WorktreeManager().dispose(
        repo_path=str(tmp_path),
        user_id="u001",
        worktree_id=created.worktree_id,
        attempt_kind="reconcile",
    )

    assert result.succeeded is True
    assert result.preflight_classification == "directory_missing"


def test_cross_scope_disposal_stops_before_executor(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    created, _, _, _ = _create_retained_worktree(tmp_path)

    class ForbiddenExecutor:
        def __getattr__(self, name: str):
            raise AssertionError(f"unexpected tool call: {name}")

    result = AgentLoop(tool_executor=ForbiddenExecutor()).run(
        AgentLoopRequest(
            message=f"confirm discard worktree {created.worktree_id}",
            repo_path=str(tmp_path),
            trace_id="trace_cross_scope",
            user_id="u002",
            session_id="s001",
        )
    )

    assert result.tool_calls == []
    assert "failed" in result.answer
    assert Path(created.execution_repo_path).exists()


def test_agent_loop_disposal_uses_only_safe_tool_call_and_persists_attempt(
    tmp_path: Path,
) -> None:
    _init_repo(tmp_path)
    created, _, _, repo_key = _create_retained_worktree(tmp_path)

    result = AgentLoop().run(
        AgentLoopRequest(
            message=f"confirm discard worktree {created.worktree_id}",
            repo_path=str(tmp_path),
            trace_id="trace_disposal",
            user_id="u001",
            session_id="s001",
        )
    )

    events = SQLiteAuditStore.for_existing_repo(tmp_path)[0].recent_events(
        user_id="u001",
        repo_key=repo_key,
        limit=20,
    )
    attempts = [event for event in events if event.event_type == "worktree_disposal"]
    public = f"{result.answer} {result.tool_calls} {result.trace_events_internal}"
    assert [call["tool_name"] for call in result.tool_calls] == ["worktree_dispose"]
    assert result.related_files == []
    assert len(attempts) == 1
    assert attempts[0].related_id == created.worktree_id
    assert str(tmp_path) not in public
    assert set(result.to_agent_result()) == {"answer", "related_files", "tool_calls"}


def test_unconfirmed_attempt_is_audited_without_tool_call(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    created, _, _, repo_key = _create_retained_worktree(tmp_path)

    result = AgentLoop().run(
        AgentLoopRequest(
            message=f"discard worktree {created.worktree_id}",
            repo_path=str(tmp_path),
            trace_id="trace_unconfirmed_disposal",
            user_id="u001",
            session_id="s001",
        )
    )

    events = SQLiteAuditStore.for_existing_repo(tmp_path)[0].recent_events(
        user_id="u001",
        repo_key=repo_key,
        limit=20,
    )
    assert result.tool_calls == []
    assert len([event for event in events if event.event_type == "worktree_disposal"]) == 1
    assert Path(created.execution_repo_path).exists()


def test_git_metadata_runner_times_out_without_retry(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0

    class TimeoutProcess:
        def wait(self, timeout=None):
            nonlocal calls
            calls += 1
            if calls == 1:
                raise subprocess.TimeoutExpired("git", timeout)
            return -9

        def kill(self):
            return None

    monkeypatch.setattr("app.worktrees.git_metadata.subprocess.Popen", lambda *a, **k: TimeoutProcess())

    assert run_git_metadata(tmp_path, "rev-parse", "HEAD", timeout=0.01) is None
    assert calls == 2


def test_git_metadata_runner_checks_size_before_reading(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class OversizeProcess:
        def __init__(self, output):
            output.write(b"x" * 12)

        def wait(self, timeout=None):
            return 0

    monkeypatch.setattr(
        "app.worktrees.git_metadata.subprocess.Popen",
        lambda *a, **k: OversizeProcess(k["stdout"]),
    )

    assert run_git_metadata(tmp_path, "rev-parse", "HEAD", max_bytes=10) is None


def test_head_mismatch_and_unsupported_lifecycle_fail_before_mutation(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    _init_repo(first)
    _init_repo(second)
    moved, _, _, _ = _create_retained_worktree(first)
    worktree = Path(moved.execution_repo_path)
    (worktree / "app.py").write_text("moved\n", encoding="utf-8")
    _git("add", "app.py", cwd=worktree)
    _git("commit", "-m", "move", cwd=worktree)
    ready, _, _, ready_key = _create_retained_worktree(second)
    ready_store = SQLiteWorktreeStore.for_existing_repo(second)[0]
    ready_store.update_worktree(
        ready.worktree_id,
        user_id="u001",
        repo_key=ready_key,
        status=WORKTREE_STATUS_READY,
    )

    mismatch = WorktreeManager().dispose(
        repo_path=str(first),
        user_id="u001",
        worktree_id=moved.worktree_id,
        attempt_kind="discard",
    )
    unsupported = WorktreeManager().dispose(
        repo_path=str(second),
        user_id="u001",
        worktree_id=ready.worktree_id,
        attempt_kind="discard",
    )

    assert mismatch.succeeded is False and mismatch.reason == "ownership_or_head_mismatch"
    assert unsupported.succeeded is False and unsupported.reason == "worktree_status_ineligible"
    assert worktree.exists()
    assert Path(ready.execution_repo_path).exists()


def test_mutation_failure_stops_and_marks_only_worktree_failed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _init_repo(tmp_path)
    created, patch_store, patch, repo_key = _create_retained_worktree(tmp_path)
    calls = 0

    def fail_once(*args, **kwargs):
        nonlocal calls
        calls += 1
        raise subprocess.CalledProcessError(1, ["git"])

    monkeypatch.setattr("app.worktrees.disposal._run_mutation", fail_once)
    result = WorktreeManager().dispose(
        repo_path=str(tmp_path),
        user_id="u001",
        worktree_id=created.worktree_id,
        attempt_kind="discard",
    )
    worktree = SQLiteWorktreeStore.for_existing_repo(tmp_path)[0].get_worktree(
        created.worktree_id,
        user_id="u001",
        repo_key=repo_key,
    )
    stored_patch = patch_store.get_patch(patch.patch_id, user_id="u001", repo_key=repo_key)

    assert result.succeeded is False
    assert result.failed_step == "unlock"
    assert calls == 1
    assert worktree is not None and worktree.status == WORKTREE_STATUS_DISPOSAL_FAILED
    assert stored_patch is not None and stored_patch.status == PATCH_STATUS_APPLIED_IN_WORKTREE


def test_store_failures_after_cleanup_stop_before_later_terminal_update(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _init_repo(tmp_path)
    created, patch_store, patch, repo_key = _create_retained_worktree(tmp_path)

    def fail_worktree_update(*args, **kwargs):
        raise OSError("private DB path")

    monkeypatch.setattr(SQLiteWorktreeStore, "update_worktree", fail_worktree_update)
    result = WorktreeManager().dispose(
        repo_path=str(tmp_path),
        user_id="u001",
        worktree_id=created.worktree_id,
        attempt_kind="discard",
    )
    stored_patch = patch_store.get_patch(patch.patch_id, user_id="u001", repo_key=repo_key)

    assert result.succeeded is False
    assert result.completed_step == "cleanup_confirmed"
    assert result.failed_step == "worktree_update"
    assert stored_patch is not None and stored_patch.status == PATCH_STATUS_APPLIED_IN_WORKTREE


def test_patch_update_failure_preserves_discarded_worktree(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _init_repo(tmp_path)
    created, _, _, repo_key = _create_retained_worktree(tmp_path)

    monkeypatch.setattr(
        SQLitePatchStore,
        "mark_status_scoped",
        lambda *args, **kwargs: False,
    )
    result = WorktreeManager().dispose(
        repo_path=str(tmp_path),
        user_id="u001",
        worktree_id=created.worktree_id,
        attempt_kind="discard",
    )
    record = SQLiteWorktreeStore.for_existing_repo(tmp_path)[0].get_worktree(
        created.worktree_id,
        user_id="u001",
        repo_key=repo_key,
    )

    assert result.succeeded is False
    assert result.completed_step == "worktree_discarded"
    assert result.failed_step == "patch_update"
    assert record is not None and record.status == WORKTREE_STATUS_DISCARDED


def test_patch_only_reconciliation_executes_no_git_or_delete(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _init_repo(tmp_path)
    created, patch_store, patch, repo_key = _create_retained_worktree(tmp_path)
    manager = WorktreeManager()
    assert manager.dispose(
        repo_path=str(tmp_path),
        user_id="u001",
        worktree_id=created.worktree_id,
        attempt_kind="discard",
    ).succeeded
    patch_store.mark_status(patch.patch_id, PATCH_STATUS_APPLIED_IN_WORKTREE)
    monkeypatch.setattr(
        "app.worktrees.disposal._run_mutation",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("no Git mutation")),
    )
    monkeypatch.setattr(
        "app.worktrees.disposal.shutil.rmtree",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("no directory deletion")),
    )

    result = manager.dispose(
        repo_path=str(tmp_path),
        user_id="u001",
        worktree_id=created.worktree_id,
        attempt_kind="reconcile",
    )

    stored_patch = patch_store.get_patch(patch.patch_id, user_id="u001", repo_key=repo_key)
    assert result.succeeded is True
    assert result.completed_step == "patch_discarded"
    assert stored_patch is not None and stored_patch.status == PATCH_STATUS_DISCARDED


def test_both_missing_reconciliation_closes_metadata_only(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    created, _, _, repo_key = _create_retained_worktree(tmp_path)
    _git(
        "worktree",
        "remove",
        "--force",
        "--force",
        created.execution_repo_path,
        cwd=tmp_path,
    )

    result = WorktreeManager().dispose(
        repo_path=str(tmp_path),
        user_id="u001",
        worktree_id=created.worktree_id,
        attempt_kind="reconcile",
    )
    record = SQLiteWorktreeStore.for_existing_repo(tmp_path)[0].get_worktree(
        created.worktree_id,
        user_id="u001",
        repo_key=repo_key,
    )

    assert result.succeeded is True
    assert result.preflight_classification == "both_missing"
    assert record is not None and record.status == WORKTREE_STATUS_DISCARDED
