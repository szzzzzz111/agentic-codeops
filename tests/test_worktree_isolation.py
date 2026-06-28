from pathlib import Path
import sqlite3
import subprocess

import app.worktrees.manager as worktree_manager_module
from app.harness.kernel import AgentLoop, AgentLoopRequest
from app.memory.store import compute_repo_key
from app.patching.store import PATCH_STATUS_APPLIED_IN_WORKTREE, SQLitePatchStore
from app.worktrees.manager import WorktreeManager
from app.worktrees.store import (
    WORKTREE_STATUS_PATCH_APPLIED,
    WORKTREE_STATUS_READY,
    WORKTREE_STATUS_VERIFICATION_FAILED,
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


def _init_git_repo(repo_path: Path) -> None:
    repo_path.mkdir(parents=True, exist_ok=True)
    _git("init", "-b", "main", cwd=repo_path)
    _git("config", "user.email", "test@example.com", cwd=repo_path)
    _git("config", "user.name", "RepoPilot Test", cwd=repo_path)
    (repo_path / ".gitignore").write_text(".repopilot/\n", encoding="utf-8")
    (repo_path / "app.py").write_text("old\n", encoding="utf-8")
    _git("add", ".gitignore", "app.py", cwd=repo_path)
    _git("commit", "-m", "init", cwd=repo_path)


def test_worktree_store_existing_repo_read_does_not_create_state(tmp_path: Path) -> None:
    _init_git_repo(tmp_path)

    existing = SQLiteWorktreeStore.for_existing_repo(tmp_path)

    assert existing is None
    assert not (tmp_path / ".repopilot").exists()


def test_worktree_manager_rejects_dirty_main_workspace(tmp_path: Path) -> None:
    _init_git_repo(tmp_path)
    (tmp_path / "app.py").write_text("dirty\n", encoding="utf-8")
    manager = WorktreeManager()

    result = manager.create(
        repo_path=str(tmp_path),
        user_id="u001",
        patch_id="patch_20260607_abcdef",
    )

    assert result.created is False
    assert result.status == "create_failed"
    assert result.reason == "workspace_not_clean"
    assert not (tmp_path / ".repopilot" / "worktrees").exists()


def test_worktree_manager_rejects_non_ignored_untracked_file(tmp_path: Path) -> None:
    _init_git_repo(tmp_path)
    (tmp_path / "notes.txt").write_text("untracked\n", encoding="utf-8")

    result = WorktreeManager().create(
        repo_path=str(tmp_path),
        user_id="u001",
        patch_id="patch_20260607_abcdef",
    )

    assert result.created is False
    assert result.reason == "workspace_not_clean"


def test_worktree_manager_allows_ignored_files(tmp_path: Path) -> None:
    _init_git_repo(tmp_path)
    ignored = tmp_path / ".repopilot" / "local.txt"
    ignored.parent.mkdir()
    ignored.write_text("ignored\n", encoding="utf-8")

    result = WorktreeManager().create(
        repo_path=str(tmp_path),
        user_id="u001",
        patch_id="patch_20260607_abcdef",
    )

    assert result.created is True


def test_worktree_manager_rolls_back_when_metadata_persistence_fails(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _init_git_repo(tmp_path)

    def fail_create_worktree(self, **kwargs):
        raise sqlite3.OperationalError("metadata unavailable")

    monkeypatch.setattr(SQLiteWorktreeStore, "create_worktree", fail_create_worktree)

    result = WorktreeManager().create(
        repo_path=str(tmp_path),
        user_id="u001",
        patch_id="patch_20260607_abcdef",
    )

    assert result.created is False
    assert result.reason == "create_failed"
    listing = _git("worktree", "list", "--porcelain", cwd=tmp_path).stdout
    assert len([line for line in listing.splitlines() if line.startswith("worktree ")]) == 1
    assert not (tmp_path / ".repopilot" / "worktrees").exists()


class _BytesPipe:
    def __init__(self, chunks: list[bytes]) -> None:
        self._chunks = list(chunks)

    def read(self, _size: int = -1) -> bytes:
        if not self._chunks:
            return b""
        return self._chunks.pop(0)


class _FakeGitProcess:
    def __init__(
        self,
        *,
        stdout_chunks: list[bytes] | None = None,
        stderr_chunks: list[bytes] | None = None,
        wait_timeout: bool = False,
        returncode: int = 0,
    ) -> None:
        self.args = ["git"]
        self.stdout = _BytesPipe(stdout_chunks or [b""])
        self.stderr = _BytesPipe(stderr_chunks or [b""])
        self.wait_timeout = wait_timeout
        self.returncode = returncode
        self.killed = False
        self.reaped = False
        self.wait_timeouts: list[object] = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        return None

    def communicate(self, input=None, timeout=None):
        return "", ""

    def poll(self) -> int:
        return self.returncode

    def wait(self, timeout=None) -> int:
        self.wait_timeouts.append(timeout)
        if self.wait_timeout and not self.killed:
            raise subprocess.TimeoutExpired(self.args, timeout)
        if self.killed:
            self.reaped = True
            return -9
        return self.returncode

    def kill(self) -> None:
        self.killed = True


def test_worktree_git_timeout_kills_reaps_and_raises(
    tmp_path: Path,
    monkeypatch,
) -> None:
    fake = _FakeGitProcess(wait_timeout=True)
    monkeypatch.setattr(
        worktree_manager_module.subprocess,
        "Popen",
        lambda *args, **kwargs: fake,
    )

    try:
        worktree_manager_module._git("status", "--porcelain", cwd=tmp_path)
    except subprocess.SubprocessError:
        pass
    else:
        raise AssertionError("expected bounded Git timeout to fail closed")

    assert fake.killed is True
    assert fake.reaped is True
    assert fake.wait_timeouts[0] is not None


def test_worktree_git_output_oversize_kills_reaps_and_raises(
    tmp_path: Path,
    monkeypatch,
) -> None:
    fake = _FakeGitProcess(stdout_chunks=[b"abcdef", b""])
    monkeypatch.setattr(worktree_manager_module, "WORKTREE_GIT_OUTPUT_MAX_BYTES", 3, raising=False)
    monkeypatch.setattr(
        worktree_manager_module.subprocess,
        "Popen",
        lambda *args, **kwargs: fake,
    )

    try:
        worktree_manager_module._git("status", "--porcelain", cwd=tmp_path)
    except subprocess.SubprocessError:
        pass
    else:
        raise AssertionError("expected bounded Git stdout oversize to fail closed")

    assert fake.killed is True
    assert fake.reaped is True


def test_worktree_git_stderr_oversize_kills_reaps_and_raises(
    tmp_path: Path,
    monkeypatch,
) -> None:
    fake = _FakeGitProcess(stderr_chunks=[b"abcdef", b""])
    monkeypatch.setattr(worktree_manager_module, "WORKTREE_GIT_OUTPUT_MAX_BYTES", 3, raising=False)
    monkeypatch.setattr(
        worktree_manager_module.subprocess,
        "Popen",
        lambda *args, **kwargs: fake,
    )

    try:
        worktree_manager_module._git("status", "--porcelain", cwd=tmp_path)
    except subprocess.SubprocessError:
        pass
    else:
        raise AssertionError("expected bounded Git stderr oversize to fail closed")

    assert fake.killed is True
    assert fake.reaped is True


def test_check_ignore_return_code_one_is_business_not_ignored(
    tmp_path: Path,
    monkeypatch,
) -> None:
    def fake_git(*args, cwd: Path, check: bool = True):
        assert check is False
        return subprocess.CompletedProcess(["git", *args], 1, "", "")

    monkeypatch.setattr(worktree_manager_module, "_git", fake_git)

    assert worktree_manager_module._is_repopilot_ignored(tmp_path) is False


def test_check_ignore_return_code_greater_than_one_fails_closed(
    tmp_path: Path,
    monkeypatch,
) -> None:
    def fake_git(*args, cwd: Path, check: bool = True):
        assert check is False
        return subprocess.CompletedProcess(["git", *args], 128, "", "fatal: bad git")

    monkeypatch.setattr(worktree_manager_module, "_git", fake_git)

    try:
        worktree_manager_module._is_repopilot_ignored(tmp_path)
    except subprocess.SubprocessError:
        pass
    else:
        raise AssertionError("expected fatal check-ignore result to fail closed")


def test_worktree_rollback_subprocess_failure_never_returns_created(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _init_git_repo(tmp_path)

    def fail_create_worktree(self, **kwargs):
        raise sqlite3.OperationalError("metadata unavailable")

    def timeout_git(*args, cwd: Path, **kwargs):
        if args[:2] in {("worktree", "unlock"), ("worktree", "remove")}:
            raise subprocess.TimeoutExpired(["git", *args], 0.01)
        return _git(*args, cwd=cwd)

    monkeypatch.setattr(SQLiteWorktreeStore, "create_worktree", fail_create_worktree)
    monkeypatch.setattr(worktree_manager_module, "_git", timeout_git)

    result = WorktreeManager().create(
        repo_path=str(tmp_path),
        user_id="u001",
        patch_id="patch_20260607_abcdef",
    )

    assert result.created is False
    assert result.reason == "create_failed"


def test_worktree_manager_id_collision_does_not_remove_existing_worktree(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _init_git_repo(tmp_path)
    manager = WorktreeManager()
    existing = manager.create(
        repo_path=str(tmp_path),
        user_id="u001",
        patch_id="patch_20260607_abcdef",
    )
    existing_path = Path(existing.execution_repo_path)
    monkeypatch.setattr(
        worktree_manager_module,
        "_new_worktree_id",
        lambda: existing.worktree_id,
    )

    collided = manager.create(
        repo_path=str(tmp_path),
        user_id="u001",
        patch_id="patch_20260607_ghijkl",
    )

    assert collided.created is False
    assert collided.reason == "create_failed"
    assert existing_path.is_dir()
    listing = _git("worktree", "list", "--porcelain", cwd=tmp_path).stdout
    assert str(existing_path).replace("\\", "/") in listing
    assert manager.get_status(
        repo_path=str(tmp_path),
        user_id="u001",
        worktree_id=existing.worktree_id,
    ) is not None


def test_worktree_manager_rejects_non_git_directory(tmp_path: Path) -> None:
    result = WorktreeManager().create(
        repo_path=str(tmp_path),
        user_id="u001",
        patch_id="patch_20260607_abcdef",
    )

    assert result.created is False
    assert result.reason == "not_git_repo"


def test_worktree_manager_rejects_bare_repo(tmp_path: Path) -> None:
    _git("init", "--bare", cwd=tmp_path)

    result = WorktreeManager().create(
        repo_path=str(tmp_path),
        user_id="u001",
        patch_id="patch_20260607_abcdef",
    )

    assert result.created is False
    assert result.reason == "bare_repo"


def test_worktree_manager_rejects_repo_without_head(tmp_path: Path) -> None:
    _git("init", "-b", "main", cwd=tmp_path)

    result = WorktreeManager().create(
        repo_path=str(tmp_path),
        user_id="u001",
        patch_id="patch_20260607_abcdef",
    )

    assert result.created is False
    assert result.reason == "missing_head"


def test_worktree_manager_rejects_when_repopilot_is_not_ignored(tmp_path: Path) -> None:
    _init_git_repo(tmp_path)
    (tmp_path / ".gitignore").write_text("", encoding="utf-8")
    _git("add", ".gitignore", cwd=tmp_path)
    _git("commit", "-m", "stop ignoring repopilot", cwd=tmp_path)

    result = WorktreeManager().create(
        repo_path=str(tmp_path),
        user_id="u001",
        patch_id="patch_20260607_abcdef",
    )

    assert result.created is False
    assert result.reason == "repopilot_not_ignored"


def test_worktree_manager_creates_detached_locked_worktree_and_persists_state(
    tmp_path: Path,
) -> None:
    _init_git_repo(tmp_path)
    manager = WorktreeManager()

    result = manager.create(
        repo_path=str(tmp_path),
        user_id="u001",
        patch_id="patch_20260607_abcdef",
    )

    assert result.created is True
    assert result.status == WORKTREE_STATUS_READY
    assert result.worktree_id.startswith("wt_")
    assert result.execution_repo_path.endswith(result.worktree_id)
    assert str(tmp_path) not in result.public_summary

    worktree_path = Path(result.execution_repo_path)
    assert worktree_path.is_dir()
    assert worktree_path.parent == tmp_path / ".repopilot" / "worktrees"

    listing = _git("worktree", "list", "--porcelain", cwd=tmp_path).stdout
    assert f"worktree {worktree_path.as_posix()}".replace("//", "/") in listing
    assert "detached" in listing
    assert "locked" in listing

    head = _git("rev-parse", "HEAD", cwd=tmp_path).stdout.strip()
    store, repo_key = SQLiteWorktreeStore.for_existing_repo(tmp_path)
    record = store.get_worktree(
        result.worktree_id,
        user_id="u001",
        repo_key=repo_key,
    )
    assert record is not None
    assert record.patch_id == "patch_20260607_abcdef"
    assert record.base_commit == head
    assert record.status == WORKTREE_STATUS_READY


def test_worktree_manager_status_query_is_scoped_by_user_and_repo(tmp_path: Path) -> None:
    _init_git_repo(tmp_path / "repo_a")
    _init_git_repo(tmp_path / "repo_b")
    manager = WorktreeManager()

    created = manager.create(
        repo_path=str(tmp_path / "repo_a"),
        user_id="u001",
        patch_id="patch_20260607_abcdef",
    )

    record = manager.get_status(
        repo_path=str(tmp_path / "repo_a"),
        user_id="u001",
        worktree_id=created.worktree_id,
    )
    other_user = manager.get_status(
        repo_path=str(tmp_path / "repo_a"),
        user_id="u002",
        worktree_id=created.worktree_id,
    )
    other_repo = manager.get_status(
        repo_path=str(tmp_path / "repo_b"),
        user_id="u001",
        worktree_id=created.worktree_id,
    )

    assert record is not None
    assert record.worktree_id == created.worktree_id
    assert other_user is None
    assert other_repo is None
    assert compute_repo_key(tmp_path / "repo_a") != compute_repo_key(tmp_path / "repo_b")


def test_worktree_manager_records_patch_and_verification_lifecycle(tmp_path: Path) -> None:
    _init_git_repo(tmp_path)
    manager = WorktreeManager()
    created = manager.create(
        repo_path=str(tmp_path),
        user_id="u001",
        patch_id="patch_20260607_abcdef",
    )

    manager.record_patch_result(
        repo_path=str(tmp_path),
        user_id="u001",
        worktree_id=created.worktree_id,
        applied=True,
        changed_files=["app.py"],
    )
    patched = manager.get_status(
        repo_path=str(tmp_path),
        user_id="u001",
        worktree_id=created.worktree_id,
    )
    assert patched is not None
    assert patched.status == WORKTREE_STATUS_PATCH_APPLIED
    assert patched.changed_files == ["app.py"]

    manager.record_verification_result(
        repo_path=str(tmp_path),
        user_id="u001",
        worktree_id=created.worktree_id,
        command_label="verify",
        succeeded=False,
    )
    verified = manager.get_status(
        repo_path=str(tmp_path),
        user_id="u001",
        worktree_id=created.worktree_id,
    )
    assert verified is not None
    assert verified.status == WORKTREE_STATUS_VERIFICATION_FAILED
    assert verified.verification_label == "verify"
    assert verified.verification_status == "failed"


def test_agent_loop_applies_patch_in_real_worktree_without_changing_main(
    tmp_path: Path,
) -> None:
    _init_git_repo(tmp_path)
    patch_store = SQLitePatchStore.for_repo(tmp_path)
    repo_key = compute_repo_key(tmp_path)
    patch = patch_store.create_pending_patch(
        user_id="u001",
        repo_key=repo_key,
        target_files=["app.py"],
        diff_text="--- a/app.py\n+++ b/app.py\n@@ -1 +1 @@\n-old\n+new\n",
        summary="update app",
    )

    result = AgentLoop().run(
        AgentLoopRequest(
            message=f"confirm patch {patch.patch_id}",
            repo_path=str(tmp_path),
            trace_id="trace_v20_real_worktree",
            user_id="u001",
            session_id="s001",
        )
    )

    assert (tmp_path / "app.py").read_text(encoding="utf-8") == "old\n"
    assert result.tool_calls[0]["tool_name"] == "worktree_create"
    assert result.tool_calls[1]["tool_name"] == "patch_apply"
    worktree_id = result.tool_calls[0]["worktree_id"]
    assert (
        tmp_path / ".repopilot" / "worktrees" / worktree_id / "app.py"
    ).read_text(encoding="utf-8") == "new\n"

    stored_patch = patch_store.get_patch(
        patch.patch_id,
        user_id="u001",
        repo_key=repo_key,
    )
    assert stored_patch is not None
    assert stored_patch.status == PATCH_STATUS_APPLIED_IN_WORKTREE
    worktree = WorktreeManager().get_status(
        repo_path=str(tmp_path),
        user_id="u001",
        worktree_id=worktree_id,
    )
    assert worktree is not None
    assert worktree.status == WORKTREE_STATUS_PATCH_APPLIED
