import subprocess
from pathlib import Path

import pytest

from app.audit.store import SQLiteAuditStore
from app.harness.kernel import AgentLoop, AgentLoopRequest
from app.memory.store import compute_repo_key
from app.patching.store import (
    PATCH_STATUS_APPLIED_IN_WORKTREE,
    PATCH_STATUS_DISCARDED,
    SQLitePatchStore,
)
from app.worktrees import disposal
from app.worktrees.disposal import parse_worktree_disposal_request
from app.worktrees.git_metadata import (
    GIT_METADATA_REAP_TIMEOUT_SECONDS,
    git_metadata_text,
    run_git_metadata,
)
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
    class TimeoutProcess:
        def __init__(self, stdout_arg):
            self.stdout_arg = stdout_arg
            self.stdout = _BytesPipe(b"")
            self.killed = False
            self.wait_calls = []

        def wait(self, timeout=None):
            self.wait_calls.append((self.killed, timeout))
            if not self.killed:
                raise subprocess.TimeoutExpired("git", timeout)
            return -9

        def kill(self):
            self.killed = True

    created = []

    def fake_popen(*args, **kwargs):
        process = TimeoutProcess(kwargs["stdout"])
        created.append(process)
        return process

    monkeypatch.setattr("app.worktrees.git_metadata.subprocess.Popen", fake_popen)

    assert run_git_metadata(tmp_path, "rev-parse", "HEAD", timeout=0.01) is None
    assert len(created) == 1
    assert created[0].stdout_arg is subprocess.PIPE
    assert created[0].killed is True
    assert created[0].wait_calls[-1] == (True, GIT_METADATA_REAP_TIMEOUT_SECONDS)


def test_git_metadata_runner_returns_none_when_process_start_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_start(*args, **kwargs):
        raise OSError("git not found")

    monkeypatch.setattr("app.worktrees.git_metadata.subprocess.Popen", fail_start)

    assert run_git_metadata(tmp_path, "rev-parse", "HEAD") is None


class _BytesPipe:
    def __init__(
        self,
        data: bytes,
        *,
        fail_read: bool = False,
        fail_read_exception: Exception | None = None,
    ):
        self._data = data
        self._offset = 0
        self._fail_read = fail_read
        self._fail_read_exception = fail_read_exception

    def read(self, size: int = -1) -> bytes:
        if self._fail_read_exception is not None:
            raise self._fail_read_exception
        if self._fail_read:
            raise OSError("pipe read failed")
        if self._offset >= len(self._data):
            return b""
        if size is None or size < 0:
            size = len(self._data) - self._offset
        chunk = self._data[self._offset : self._offset + size]
        self._offset += len(chunk)
        return chunk

    def close(self) -> None:
        return None


class _MutationProcess:
    def __init__(
        self,
        *,
        stdout: bytes = b"",
        stderr: bytes = b"",
        return_code: int = 0,
        block_until_killed: bool = False,
        fail_stdout_read: bool = False,
        fail_stderr_read: bool = False,
        fail_stdout_read_exception: Exception | None = None,
        fail_stderr_read_exception: Exception | None = None,
    ):
        self.stdout_arg = None
        self.stderr_arg = None
        self.stdout = _BytesPipe(
            stdout,
            fail_read=fail_stdout_read,
            fail_read_exception=fail_stdout_read_exception,
        )
        self.stderr = _BytesPipe(
            stderr,
            fail_read=fail_stderr_read,
            fail_read_exception=fail_stderr_read_exception,
        )
        self.return_code = return_code
        self.block_until_killed = block_until_killed
        self.killed = False
        self.wait_calls = []

    def wait(self, timeout=None):
        self.wait_calls.append((self.killed, timeout))
        if self.killed:
            return -9
        if self.block_until_killed:
            raise subprocess.TimeoutExpired("git", timeout)
        return self.return_code

    def kill(self):
        self.killed = True


def _forbid_disposal_subprocess_run(monkeypatch: pytest.MonkeyPatch) -> None:
    def forbidden_run(*args, **kwargs):
        raise AssertionError("disposal mutations must use bounded Popen runner")

    monkeypatch.setattr(disposal.subprocess, "run", forbidden_run)


def _install_mutation_process(
    monkeypatch: pytest.MonkeyPatch,
    process: _MutationProcess,
    *,
    command_log: list[tuple[tuple, dict]] | None = None,
) -> None:
    def fake_popen(*args, **kwargs):
        process.stdout_arg = kwargs.get("stdout")
        process.stderr_arg = kwargs.get("stderr")
        if command_log is not None:
            command_log.append((args, kwargs))
        return process

    monkeypatch.setattr(disposal.subprocess, "Popen", fake_popen)
    _forbid_disposal_subprocess_run(monkeypatch)


def test_mutation_runner_uses_fixed_argv_shell_false_and_locks_disabled(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    process = _MutationProcess()
    command_log = []
    _install_mutation_process(monkeypatch, process, command_log=command_log)

    disposal._run_mutation(tmp_path, "worktree", "unlock", "example")

    assert len(command_log) == 1
    args, kwargs = command_log[0]
    assert args[0] == ["git", "worktree", "unlock", "example"]
    assert kwargs["cwd"] == tmp_path
    assert kwargs["shell"] is False
    assert kwargs["stdout"] is subprocess.PIPE
    assert kwargs["stderr"] is subprocess.PIPE
    assert kwargs["env"]["GIT_OPTIONAL_LOCKS"] == "0"
    assert process.stdout_arg is subprocess.PIPE
    assert process.stderr_arg is subprocess.PIPE


def test_mutation_runner_times_out_and_reaps_without_retry(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    process = _MutationProcess(block_until_killed=True)
    _install_mutation_process(monkeypatch, process)
    monkeypatch.setattr(disposal, "WORKTREE_DISPOSAL_MUTATION_TIMEOUT_SECONDS", 0.01, raising=False)

    with pytest.raises(subprocess.SubprocessError):
        disposal._run_mutation(tmp_path, "worktree", "remove", "--force", "example")

    assert process.killed is True
    assert process.wait_calls[-1] == (
        True,
        disposal.WORKTREE_DISPOSAL_MUTATION_REAP_TIMEOUT_SECONDS,
    )


@pytest.mark.parametrize(
    ("stream_name", "stdout", "stderr"),
    [
        ("stdout", b"x" * 12, b""),
        ("stderr", b"", b"y" * 12),
    ],
)
def test_mutation_runner_kills_oversize_stdout_or_stderr_without_exposing_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    stream_name: str,
    stdout: bytes,
    stderr: bytes,
) -> None:
    process = _MutationProcess(stdout=stdout, stderr=stderr, block_until_killed=True)
    _install_mutation_process(monkeypatch, process)
    monkeypatch.setattr(disposal, "WORKTREE_DISPOSAL_MUTATION_OUTPUT_MAX_BYTES", 10, raising=False)

    with pytest.raises(subprocess.SubprocessError) as excinfo:
        disposal._run_mutation(tmp_path, "worktree", "unlock", "example")

    assert process.killed is True
    assert stream_name in str(excinfo.value)
    assert "xxxxxxxx" not in str(excinfo.value)
    assert "yyyyyyyy" not in str(excinfo.value)


def test_mutation_runner_rejects_pipe_read_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    process = _MutationProcess(fail_stderr_read=True)
    _install_mutation_process(monkeypatch, process)

    with pytest.raises(subprocess.SubprocessError):
        disposal._run_mutation(tmp_path, "worktree", "unlock", "example")

    assert process.killed is True


def test_mutation_runner_rejects_unexpected_pipe_read_exception(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    process = _MutationProcess(fail_stdout_read_exception=RuntimeError("traceback C:\\secret"))
    _install_mutation_process(monkeypatch, process)

    with pytest.raises(subprocess.SubprocessError) as excinfo:
        disposal._run_mutation(tmp_path, "worktree", "unlock", "example")

    assert process.killed is True
    assert "traceback" not in str(excinfo.value)
    assert "secret" not in str(excinfo.value)


def test_mutation_runner_rejects_reader_non_completion(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    process = _MutationProcess()
    _install_mutation_process(monkeypatch, process)

    class NeverFinishingReader:
        def __init__(self, *args, **kwargs):
            self.join_calls = []

        def start(self):
            return None

        def join(self, timeout=None):
            self.join_calls.append(timeout)

        def is_alive(self):
            return True

    monkeypatch.setattr(disposal.threading, "Thread", NeverFinishingReader)

    with pytest.raises(subprocess.SubprocessError) as excinfo:
        disposal._run_mutation(tmp_path, "worktree", "unlock", "example")

    assert process.killed is True
    assert "reader_incomplete" in str(excinfo.value)


def test_mutation_runner_process_start_failure_is_safe(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_start(*args, **kwargs):
        raise OSError(f"missing git at {tmp_path}\\secret\\git.exe")

    monkeypatch.setattr(disposal.subprocess, "Popen", fail_start)
    _forbid_disposal_subprocess_run(monkeypatch)

    with pytest.raises(subprocess.SubprocessError) as excinfo:
        disposal._run_mutation(tmp_path, "worktree", "unlock", "example")

    assert str(tmp_path) not in str(excinfo.value)
    assert "secret" not in str(excinfo.value)


def test_mutation_runner_nonzero_exit_is_safe_and_bounded(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    process = _MutationProcess(stderr=f"fatal path {tmp_path}\\repo.sqlite3".encode(), return_code=128)
    _install_mutation_process(monkeypatch, process)

    with pytest.raises(subprocess.SubprocessError) as excinfo:
        disposal._run_mutation(tmp_path, "worktree", "unlock", "example")

    assert process.wait_calls
    assert str(tmp_path) not in str(excinfo.value)
    assert "repo.sqlite3" not in str(excinfo.value)


def test_git_metadata_runner_kills_oversize_output_before_full_wait(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class BlockingOversizeProcess:
        def __init__(self, stdout_arg):
            self.stdout_arg = stdout_arg
            self.stdout = _BytesPipe(b"x" * 12)
            self.killed = False
            self.wait_calls = []

        def wait(self, timeout=None):
            self.wait_calls.append((self.killed, timeout))
            if self.killed:
                return -9
            raise subprocess.TimeoutExpired("git", timeout)

        def kill(self):
            self.killed = True

    created = []

    def fake_popen(*args, **kwargs):
        process = BlockingOversizeProcess(kwargs["stdout"])
        created.append(process)
        return process

    monkeypatch.setattr(
        "app.worktrees.git_metadata.subprocess.Popen",
        fake_popen,
    )

    assert run_git_metadata(tmp_path, "rev-parse", "HEAD", timeout=1.0, max_bytes=10) is None
    assert created[0].stdout_arg is subprocess.PIPE
    assert created[0].killed is True
    pre_kill_waits = [timeout for killed, timeout in created[0].wait_calls if not killed]
    assert all(timeout < 1.0 for timeout in pre_kill_waits)
    assert created[0].wait_calls[-1] == (True, GIT_METADATA_REAP_TIMEOUT_SECONDS)


def test_git_metadata_runner_rejects_pipe_read_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class ReadFailureProcess:
        def __init__(self, stdout_arg):
            self.stdout_arg = stdout_arg
            self.stdout = _BytesPipe(b"", fail_read=True)
            self.killed = False

        def wait(self, timeout=None):
            return -9 if self.killed else 0

        def kill(self):
            self.killed = True

    created = []

    def fake_popen(*args, **kwargs):
        process = ReadFailureProcess(kwargs["stdout"])
        created.append(process)
        return process

    monkeypatch.setattr("app.worktrees.git_metadata.subprocess.Popen", fake_popen)

    assert run_git_metadata(tmp_path, "rev-parse", "HEAD") is None
    assert created[0].stdout_arg is subprocess.PIPE
    assert created[0].killed is True


def test_git_metadata_runner_preserves_cap_edge_and_nonzero_exit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class PipeProcess:
        def __init__(self, stdout_arg, data: bytes, return_code: int = 0):
            self.stdout_arg = stdout_arg
            self.stdout = _BytesPipe(data)
            self.return_code = return_code
            self.killed = False

        def wait(self, timeout=None):
            return -9 if self.killed else self.return_code

        def kill(self):
            self.killed = True

    created = []
    outputs = [b"x" * 10, b"x" * 11, b"ok"]
    return_codes = [0, 0, 1]

    def fake_popen(*args, **kwargs):
        process = PipeProcess(kwargs["stdout"], outputs.pop(0), return_codes.pop(0))
        created.append(process)
        return process

    monkeypatch.setattr("app.worktrees.git_metadata.subprocess.Popen", fake_popen)

    assert run_git_metadata(tmp_path, "rev-parse", "HEAD", max_bytes=10) == b"x" * 10
    assert run_git_metadata(tmp_path, "rev-parse", "HEAD", max_bytes=10) is None
    assert run_git_metadata(tmp_path, "rev-parse", "HEAD", max_bytes=10) is None
    assert all(process.stdout_arg is subprocess.PIPE for process in created)


def test_git_metadata_text_rejects_invalid_utf8(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "app.worktrees.git_metadata.run_git_metadata",
        lambda *args, **kwargs: b"locked \xff",
    )

    assert git_metadata_text(tmp_path, "worktree", "list", "--porcelain", "-z") is None


def test_reconcile_rejects_registry_path_mismatch_without_mutation(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    created, patch_store, patch, repo_key = _create_retained_worktree(tmp_path)
    original = Path(created.execution_repo_path)
    moved = original.parent / "moved_elsewhere"
    _git("worktree", "unlock", str(original), cwd=tmp_path)
    _git("worktree", "move", str(original), str(moved), cwd=tmp_path)

    result = WorktreeManager().dispose(
        repo_path=str(tmp_path),
        user_id="u001",
        worktree_id=created.worktree_id,
        attempt_kind="reconcile",
    )

    stored_worktree = SQLiteWorktreeStore.for_existing_repo(tmp_path)[0].get_worktree(
        created.worktree_id,
        user_id="u001",
        repo_key=repo_key,
    )
    stored_patch = patch_store.get_patch(patch.patch_id, user_id="u001", repo_key=repo_key)
    assert result.succeeded is False
    assert result.reason == "registry_path_mismatch"
    assert result.mutation_attempted is False
    assert moved.exists()
    assert stored_worktree is not None and stored_worktree.status != WORKTREE_STATUS_DISCARDED
    assert stored_patch is not None and stored_patch.status == PATCH_STATUS_APPLIED_IN_WORKTREE


def test_reconcile_rejects_admin_backref_registry_inconsistency(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _init_repo(tmp_path)
    created, _, _, _ = _create_retained_worktree(tmp_path)
    monkeypatch.setattr("app.worktrees.disposal.registry_entries", lambda repo_root: {})

    result = WorktreeManager().dispose(
        repo_path=str(tmp_path),
        user_id="u001",
        worktree_id=created.worktree_id,
        attempt_kind="reconcile",
    )

    assert result.succeeded is False
    assert result.reason == "metadata_invalid"
    assert result.mutation_attempted is False
    assert Path(created.execution_repo_path).exists()


@pytest.mark.parametrize("database_name", ["worktrees.sqlite3", "patches.sqlite3"])
def test_damaged_scoped_metadata_fails_closed_and_audits_attempt(
    tmp_path: Path,
    database_name: str,
) -> None:
    _init_repo(tmp_path)
    created, _, _, repo_key = _create_retained_worktree(tmp_path)
    (tmp_path / ".repopilot" / database_name).write_bytes(b"not sqlite")

    result = AgentLoop().run(
        AgentLoopRequest(
            message=f"confirm discard worktree {created.worktree_id}",
            repo_path=str(tmp_path),
            trace_id="trace_damaged_worktree_metadata",
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
    assert "failed" in result.answer
    assert "metadata_invalid" in result.answer
    assert result.tool_calls == []
    assert Path(created.execution_repo_path).exists()
    assert len(attempts) == 1


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


def test_mutation_failure_does_not_expose_sensitive_output_or_paths(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _init_repo(tmp_path)
    created, _, _, repo_key = _create_retained_worktree(tmp_path)
    sensitive_values = [
        str(tmp_path),
        "raw stderr payload",
        "Traceback (most recent call last)",
        "repo.sqlite3",
        "diff --git a/app.py b/app.py",
    ]

    def fail_with_sensitive_details(*args, **kwargs):
        raise subprocess.SubprocessError("; ".join(sensitive_values))

    monkeypatch.setattr("app.worktrees.disposal._run_mutation", fail_with_sensitive_details)
    result = AgentLoop().run(
        AgentLoopRequest(
            message=f"confirm discard worktree {created.worktree_id}",
            repo_path=str(tmp_path),
            trace_id="trace_sensitive_disposal_failure",
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
    audit_text = " ".join(f"{event.summary} {event.payload}" for event in attempts)

    assert "mutation_failed" in public
    assert len(attempts) == 1
    assert "mutation_failed" in audit_text
    for value in sensitive_values:
        assert value not in public
        assert value not in audit_text


def test_disposal_result_public_summary_does_not_expose_sensitive_mutation_details(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _init_repo(tmp_path)
    created, _, _, _ = _create_retained_worktree(tmp_path)

    def fail_with_sensitive_details(*args, **kwargs):
        raise subprocess.SubprocessError(
            f"raw stderr payload; Traceback (most recent call last); {tmp_path}\\repo.sqlite3"
        )

    monkeypatch.setattr("app.worktrees.disposal._run_mutation", fail_with_sensitive_details)
    result = WorktreeManager().dispose(
        repo_path=str(tmp_path),
        user_id="u001",
        worktree_id=created.worktree_id,
        attempt_kind="discard",
    )

    assert "mutation_failed" in result.public_summary
    assert "raw stderr payload" not in result.public_summary
    assert "Traceback" not in result.public_summary
    assert str(tmp_path) not in result.public_summary
    assert "repo.sqlite3" not in result.public_summary


def test_postcheck_metadata_unavailability_after_mutation_is_failed_disposal(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _init_repo(tmp_path)
    created, patch_store, patch, repo_key = _create_retained_worktree(tmp_path)
    from app.worktrees import disposal

    real_registry_entries = disposal.registry_entries
    calls = 0

    def fail_after_preflight(repo_root):
        nonlocal calls
        calls += 1
        if calls == 1:
            return real_registry_entries(repo_root)
        return None

    monkeypatch.setattr("app.worktrees.disposal.registry_entries", fail_after_preflight)

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
    assert result.reason == "mutation_failed"
    assert result.completed_step == "remove"
    assert result.failed_step == "postcheck"
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


def test_both_missing_reconciliation_ignores_other_registered_worktrees(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    removed, _, _, _ = _create_retained_worktree(tmp_path)
    retained, _, _, _ = _create_retained_worktree(tmp_path)
    _git(
        "worktree",
        "remove",
        "--force",
        "--force",
        removed.execution_repo_path,
        cwd=tmp_path,
    )

    result = WorktreeManager().dispose(
        repo_path=str(tmp_path),
        user_id="u001",
        worktree_id=removed.worktree_id,
        attempt_kind="reconcile",
    )

    assert result.succeeded is True
    assert result.preflight_classification == "both_missing"
    assert Path(retained.execution_repo_path).exists()
