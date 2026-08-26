import subprocess
from pathlib import Path

import pytest

from app.audit.store import SQLiteAuditStore
from app.harness.kernel import AgentLoop, AgentLoopRequest
from app.memory.store import compute_repo_key
from app.worktrees import inspection as worktree_inspection
from app.worktrees.manager import WorktreeManager
from app.worktrees.store import SQLiteWorktreeStore


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
    (repo / ".gitignore").write_text(".repopilot/\n.env\n", encoding="utf-8")
    (repo / "app.py").write_text("old\n", encoding="utf-8")
    _git("add", ".gitignore", "app.py", cwd=repo)
    _git("commit", "-m", "init", cwd=repo)


def _create_worktree(repo: Path, *, user_id: str = "u001"):
    return WorktreeManager().create(
        repo_path=str(repo),
        user_id=user_id,
        patch_id="patch_20260609_abcdef",
    )


def test_inventory_missing_store_does_not_create_state(tmp_path: Path) -> None:
    _init_repo(tmp_path)

    result = WorktreeManager().inventory(repo_path=str(tmp_path), user_id="u001")

    assert result.records == []
    assert result.store_present is False
    assert not (tmp_path / ".repopilot").exists()


def test_readonly_git_and_store_use_no_write_modes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    popen_call: dict[str, object] = {}
    sqlite_call: dict[str, object] = {}

    class FakeProcess:
        pass

    def fake_popen(*args, **kwargs):
        popen_call.update(kwargs)
        return FakeProcess()

    def fake_connect(*args, **kwargs):
        sqlite_call["args"] = args
        sqlite_call.update(kwargs)
        return object()

    monkeypatch.setattr(worktree_inspection.subprocess, "Popen", fake_popen)
    monkeypatch.setattr("app.worktrees.store.sqlite3.connect", fake_connect)

    worktree_inspection._popen_git(tmp_path, "status", "--porcelain=v1")
    SQLiteWorktreeStore(tmp_path / "worktrees.sqlite3", initialize=False)._connect_readonly()

    assert popen_call["shell"] is False
    assert popen_call["env"]["GIT_OPTIONAL_LOCKS"] == "0"
    assert "mode=ro&immutable=1" in sqlite_call["args"][0]
    assert sqlite_call["uri"] is True


def test_inventory_is_scoped_limited_and_stably_ordered(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    store, repo_key = SQLiteWorktreeStore.for_repo(tmp_path)
    for index in range(25):
        store.create_worktree(
            user_id="u001",
            repo_key=repo_key,
            worktree_id=f"wt_20260609_{index:06d}",
            patch_id=f"patch_20260609_{index:06d}",
            base_commit="a" * 40,
            status="ready",
        )
    store.create_worktree(
        user_id="u002",
        repo_key=repo_key,
        worktree_id="wt_20260609_other",
        patch_id="patch_20260609_other",
        base_commit="b" * 40,
        status="ready",
    )

    result = WorktreeManager().inventory(repo_path=str(tmp_path), user_id="u001")

    assert len(result.records) == 20
    assert result.records[0].worktree_id == "wt_20260609_000024"
    assert result.records[-1].worktree_id == "wt_20260609_000005"
    assert all(record.user_id == "u001" for record in result.records)


def test_inspection_reports_git_consistency_stats_preview_and_untracked_count(
    tmp_path: Path,
) -> None:
    _init_repo(tmp_path)
    created = _create_worktree(tmp_path)
    worktree = Path(created.execution_repo_path)
    (worktree / "app.py").write_text("new\nsecond\n", encoding="utf-8")
    (worktree / "private-token.txt").write_text("API_TOKEN=hidden\n", encoding="utf-8")

    result = WorktreeManager().inspect(
        repo_path=str(tmp_path),
        user_id="u001",
        worktree_id=created.worktree_id,
    )

    assert result.found is True
    assert result.metadata_valid is True
    assert result.directory_present is True
    assert result.git_registry_present is True
    assert result.registry_path_matches_expected is True
    assert result.head_matches_base_commit is True
    assert result.changed_files == ["app.py"]
    assert result.additions == 2
    assert result.deletions == 1
    assert result.hunk_count == 1
    assert result.untracked_count == 1
    assert "app.py" in result.preview
    assert "+new" in result.preview
    assert "private-token.txt" not in result.preview
    assert "API_TOKEN=hidden" not in result.preview


def test_inspection_uses_git_paths_not_metadata_changed_files(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    created = _create_worktree(tmp_path)
    worktree = Path(created.execution_repo_path)
    (worktree / "app.py").write_text("new\n", encoding="utf-8")
    store, repo_key = SQLiteWorktreeStore.for_existing_repo(tmp_path)
    store.update_worktree(
        created.worktree_id,
        user_id="u001",
        repo_key=repo_key,
        status="patch_applied",
        changed_files=["not-from-git.txt"],
    )

    result = WorktreeManager().inspect(
        repo_path=str(tmp_path),
        user_id="u001",
        worktree_id=created.worktree_id,
    )

    assert result.changed_files == ["app.py"]
    assert "not-from-git.txt" not in result.preview


def test_inspection_preview_is_bounded_and_redacted(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    created = _create_worktree(tmp_path)
    worktree = Path(created.execution_repo_path)
    long_line = "x" * 10_000
    content = "\n".join(
        [
            "API_KEY=super-secret",
            "db=.repopilot/audit.sqlite3",
            f"C:/Users/person/project/{long_line}",
            *[f"line-{index}" for index in range(100)],
        ]
    )
    (worktree / "app.py").write_text(content + "\n", encoding="utf-8")

    result = WorktreeManager().inspect(
        repo_path=str(tmp_path),
        user_id="u001",
        worktree_id=created.worktree_id,
    )

    assert len(result.preview) <= 6000
    assert all(len(line) <= 300 for line in result.preview.splitlines())
    assert "super-secret" not in result.preview
    assert ".repopilot/audit.sqlite3" not in result.preview
    assert "C:/Users/person" not in result.preview
    assert result.truncated_lines > 0


def test_inspection_preview_limits_files_and_omits_unsafe_content(
    tmp_path: Path,
) -> None:
    _init_repo(tmp_path)
    for index in range(22):
        (tmp_path / f"file-{index:02d}.txt").write_text("old\n", encoding="utf-8")
    (tmp_path / ".hidden.txt").write_text("old hidden\n", encoding="utf-8")
    (tmp_path / "secret.pem").write_text("old secret\n", encoding="utf-8")
    (tmp_path / "binary.dat").write_bytes(b"old\0binary")
    _git("add", ".", cwd=tmp_path)
    _git("commit", "-m", "add preview fixtures", cwd=tmp_path)
    created = _create_worktree(tmp_path)
    worktree = Path(created.execution_repo_path)
    for index in range(22):
        (worktree / f"file-{index:02d}.txt").write_text("new\n", encoding="utf-8")
    (worktree / ".hidden.txt").write_text("new hidden\n", encoding="utf-8")
    (worktree / "secret.pem").write_text("API_KEY=unsafe\n", encoding="utf-8")
    (worktree / "binary.dat").write_bytes(b"new\0binary")

    result = WorktreeManager().inspect(
        repo_path=str(tmp_path),
        user_id="u001",
        worktree_id=created.worktree_id,
    )

    assert result.omitted_files == 5
    assert "file-00.txt" in result.preview
    assert "file-20.txt" not in result.preview
    assert "file-21.txt" not in result.preview
    assert ".hidden.txt" not in result.preview
    assert "secret.pem" not in result.preview
    assert "binary.dat" not in result.preview
    assert "API_KEY=unsafe" not in result.preview


def test_agent_loop_reports_omitted_counts_when_preview_is_empty(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    (tmp_path / "secret.pem").write_text("old secret\n", encoding="utf-8")
    (tmp_path / "binary.dat").write_bytes(b"old\0binary")
    _git("add", ".", cwd=tmp_path)
    _git("commit", "-m", "add unsafe fixtures", cwd=tmp_path)
    created = _create_worktree(tmp_path)
    worktree = Path(created.execution_repo_path)
    (worktree / "secret.pem").write_text("API_KEY=unsafe\n", encoding="utf-8")
    (worktree / "binary.dat").write_bytes(b"new\0binary")

    result = AgentLoop().run(
        AgentLoopRequest(
            message=f"worktree status {created.worktree_id}",
            repo_path=str(tmp_path),
            trace_id="trace_empty_preview",
            user_id="u001",
            session_id="s001",
        )
    )

    assert "\npreview:\n" not in result.answer
    assert "binary_files=1" in result.answer
    assert "preview_limits: omitted_files=2" in result.answer
    assert "API_KEY=unsafe" not in result.answer


def test_inspection_unknown_scope_stops_without_git_or_state(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    created = _create_worktree(tmp_path, user_id="u001")

    result = WorktreeManager().inspect(
        repo_path=str(tmp_path),
        user_id="u002",
        worktree_id=created.worktree_id,
    )

    assert result.found is False
    assert result.git_registry_present is False
    assert result.preview == ""


def test_inspection_rejects_unsafe_metadata_before_git(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    store, repo_key = SQLiteWorktreeStore.for_repo(tmp_path)
    store.create_worktree(
        user_id="u001",
        repo_key=repo_key,
        worktree_id="../escaped",
        patch_id="patch_20260609_unsafe",
        base_commit="--output=outside",
        status="ready",
    )
    escaped = tmp_path / ".repopilot" / "escaped"
    escaped.mkdir()
    (escaped / "secret.txt").write_text("API_KEY=do-not-read\n", encoding="utf-8")

    result = WorktreeManager().inspect(
        repo_path=str(tmp_path),
        user_id="u001",
        worktree_id="../escaped",
    )

    assert result.found is True
    assert result.partial is True
    assert result.metadata_valid is False
    assert result.directory_present is False
    assert result.changed_files == []
    assert result.preview == ""


def test_inspection_git_start_failure_returns_safe_partial(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _init_repo(tmp_path)
    created = _create_worktree(tmp_path)

    def fail_git(*args, **kwargs):
        raise OSError("git unavailable at C:/secret/path")

    monkeypatch.setattr("app.worktrees.inspection._popen_git", fail_git)

    result = WorktreeManager().inspect(
        repo_path=str(tmp_path),
        user_id="u001",
        worktree_id=created.worktree_id,
    )

    assert result.found is True
    assert result.partial is True
    assert result.changed_files == []
    assert result.preview == ""


def test_stream_hunk_count_timeout_kills_reaps_and_returns_partial(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeStdout:
        def __init__(self) -> None:
            self._lines = [b"@@ -1 +1 @@\n", b""]

        def readline(self, _size: int = -1) -> bytes:
            return self._lines.pop(0)

    class FakeProcess:
        def __init__(self) -> None:
            self.stdout = FakeStdout()
            self.killed = False
            self.wait_timeouts: list[object] = []

        def wait(self, timeout=None):
            self.wait_timeouts.append(timeout)
            if self.killed:
                return -9
            raise subprocess.TimeoutExpired(["git", "diff"], timeout)

        def kill(self) -> None:
            self.killed = True

    fake = FakeProcess()
    monkeypatch.setattr("app.worktrees.inspection._popen_git", lambda *args: fake)

    count, partial = worktree_inspection._stream_hunk_count(tmp_path, "a" * 40)

    assert count == 1
    assert partial is True
    assert fake.killed is True
    assert fake.wait_timeouts[0] is not None


def test_stream_hunk_count_watchdog_read_timeout_kills_reaps_and_returns_partial(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    timers = []

    class ImmediateTimer:
        def __init__(self, _interval: float, callback) -> None:
            self.callback = callback
            self.daemon = False
            self.started = False
            self.cancelled = False
            timers.append(self)

        def start(self) -> None:
            self.started = True
            self.callback()

        def cancel(self) -> None:
            self.cancelled = True

    class WatchdogClosedStdout:
        def __init__(self, process) -> None:
            self.process = process

        def readline(self, _size: int = -1) -> bytes:
            assert self.process.killed is True
            return b""

    class FakeProcess:
        def __init__(self) -> None:
            self.killed = False
            self.reaped = False
            self.stdout = WatchdogClosedStdout(self)

        def wait(self, timeout=None):
            if self.killed:
                self.reaped = True
                return -9
            return 0

        def kill(self) -> None:
            self.killed = True

    fake = FakeProcess()
    monkeypatch.setattr("app.worktrees.inspection._popen_git", lambda *args: fake)
    monkeypatch.setattr("app.worktrees.inspection.threading.Timer", ImmediateTimer)

    count, partial = worktree_inspection._stream_hunk_count(tmp_path, "a" * 40)

    assert count == 0
    assert partial is True
    assert fake.killed is True
    assert fake.reaped is True
    assert timers[0].started is True
    assert timers[0].cancelled is True


def test_preview_timeout_omits_affected_file_and_returns_partial(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (tmp_path / "app.py").write_text("safe\n", encoding="utf-8")

    class FakeStdout:
        def __init__(self) -> None:
            self._lines = [b"diff --git a/app.py b/app.py\n", b"+new\n", b""]

        def readline(self, _size: int = -1) -> bytes:
            return self._lines.pop(0)

    class FakeProcess:
        def __init__(self) -> None:
            self.stdout = FakeStdout()
            self.killed = False

        def wait(self, timeout=None):
            if self.killed:
                return -9
            raise subprocess.TimeoutExpired(["git", "diff"], timeout)

        def kill(self) -> None:
            self.killed = True

    fake = FakeProcess()
    monkeypatch.setattr("app.worktrees.inspection._popen_git", lambda *args: fake)

    preview, omitted, truncated_files, truncated_lines, truncated_chars, partial = (
        worktree_inspection._format_preview(tmp_path, "a" * 40, ["app.py"])
    )

    assert preview == ""
    assert omitted == 1
    assert truncated_files == 0
    assert truncated_lines == 0
    assert truncated_chars == 0
    assert partial is True
    assert fake.killed is True


def test_inspection_metadata_cap_returns_safe_partial(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _init_repo(tmp_path)
    created = _create_worktree(tmp_path)
    worktree = Path(created.execution_repo_path)
    (worktree / "app.py").write_text("new\n", encoding="utf-8")
    monkeypatch.setattr("app.worktrees.inspection.MAX_METADATA_BYTES", 1)

    result = WorktreeManager().inspect(
        repo_path=str(tmp_path),
        user_id="u001",
        worktree_id=created.worktree_id,
    )

    assert result.partial is True
    assert result.changed_files == []
    assert result.preview == ""


def test_agent_loop_missing_inventory_and_inspection_create_no_state(
    tmp_path: Path,
) -> None:
    _init_repo(tmp_path)
    loop = AgentLoop()

    inventory = loop.run(
        AgentLoopRequest(
            message="worktree list",
            repo_path=str(tmp_path),
            trace_id="trace_missing_inventory",
            user_id="u001",
            session_id="s001",
        )
    )
    inspection = loop.run(
        AgentLoopRequest(
            message="worktree status wt_20260609_abcdef",
            repo_path=str(tmp_path),
            trace_id="trace_missing_inspection",
            user_id="u001",
            session_id="s001",
        )
    )

    assert "当前 scope worktrees: 0" in inventory.answer
    assert "未找到 worktree_id=wt_20260609_abcdef" in inspection.answer
    assert not (tmp_path / ".repopilot").exists()


def test_agent_loop_bounds_and_redacts_worktree_metadata(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    store, repo_key = SQLiteWorktreeStore.for_repo(tmp_path)
    store.create_worktree(
        user_id="u001",
        repo_key=repo_key,
        worktree_id="wt_20260609_metadata",
        patch_id="API_KEY=inventory-secret\n" + ("x" * 500),
        base_commit="a" * 40,
        status="C:/Users/person/private/status",
        verification_label=".repopilot/audit.sqlite3",
        verification_status="PASSWORD=inspection-secret",
    )

    inventory = AgentLoop().run(
        AgentLoopRequest(
            message="worktree list",
            repo_path=str(tmp_path),
            trace_id="trace_metadata_inventory",
            user_id="u001",
            session_id="s001",
        )
    )
    inspection = AgentLoop().run(
        AgentLoopRequest(
            message="worktree status wt_20260609_metadata",
            repo_path=str(tmp_path),
            trace_id="trace_metadata_inspection",
            user_id="u001",
            session_id="s001",
        )
    )

    combined = inventory.answer + inspection.answer
    assert "inventory-secret" not in combined
    assert "inspection-secret" not in combined
    assert "C:/Users/person" not in combined
    assert ".repopilot/audit.sqlite3" not in combined
    assert "\nxxxxxxxx" not in combined
    assert len(inventory.answer) < 1000
    assert len(inspection.answer) < 1500


def test_agent_loop_bounds_tracked_changed_file_summary(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    for index in range(25):
        path = tmp_path / f"tracked-{index:02d}-{'x' * 80}.txt"
        path.write_text("old\n", encoding="utf-8")
    _git("add", ".", cwd=tmp_path)
    _git("commit", "-m", "add tracked fixtures", cwd=tmp_path)
    created = _create_worktree(tmp_path)
    worktree = Path(created.execution_repo_path)
    for path in worktree.glob("tracked-*.txt"):
        path.write_text("new\n", encoding="utf-8")

    result = AgentLoop().run(
        AgentLoopRequest(
            message=f"worktree status {created.worktree_id}",
            repo_path=str(tmp_path),
            trace_id="trace_changed_files_bound",
            user_id="u001",
            session_id="s001",
        )
    )

    assert "changed_files_omitted=5" in result.answer
    assert "tracked-19-" in result.answer
    assert "tracked-20-" not in result.answer
    assert len(result.answer) < 10_000


def test_agent_loop_corrupt_worktree_store_returns_safe_read_result(
    tmp_path: Path,
) -> None:
    _init_repo(tmp_path)
    state_dir = tmp_path / ".repopilot"
    state_dir.mkdir()
    (state_dir / "worktrees.sqlite3").write_text("not sqlite", encoding="utf-8")
    loop = AgentLoop()

    inventory = loop.run(
        AgentLoopRequest(
            message="worktree list",
            repo_path=str(tmp_path),
            trace_id="trace_corrupt_inventory",
            user_id="u001",
            session_id="s001",
        )
    )
    inspection = loop.run(
        AgentLoopRequest(
            message="worktree status wt_20260609_abcdef",
            repo_path=str(tmp_path),
            trace_id="trace_corrupt_inspection",
            user_id="u001",
            session_id="s001",
        )
    )

    assert "当前 scope worktrees: 0" in inventory.answer
    assert "未找到 worktree_id=wt_20260609_abcdef" in inspection.answer


def test_agent_loop_inventory_and_inspection_skip_persistent_audit(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    created = _create_worktree(tmp_path)
    WorktreeManager().record_verification_result(
        repo_path=str(tmp_path),
        user_id="u001",
        worktree_id=created.worktree_id,
        command_label="verify",
        succeeded=True,
    )
    audit_store, repo_key = SQLiteAuditStore.for_repo(tmp_path)
    audit_store.insert_event(
        event_type="trace",
        user_id="u001",
        repo_key=repo_key,
        status="ok",
        summary="existing",
        payload={},
    )

    inventory = AgentLoop().run(
        AgentLoopRequest(
            message="worktree list",
            repo_path=str(tmp_path),
            trace_id="trace_inventory",
            user_id="u001",
            session_id="s001",
        )
    )
    inspection = AgentLoop().run(
        AgentLoopRequest(
            message=f"worktree status {created.worktree_id} user-path.txt",
            repo_path=str(tmp_path),
            trace_id="trace_inspection",
            user_id="u001",
            session_id="s001",
        )
    )

    events = audit_store.recent_events(user_id="u001", repo_key=repo_key, limit=20)
    assert len(events) == 1
    assert inventory.tool_calls == []
    assert inspection.tool_calls == []
    assert any(
        event.event_type == "worktree_inventory"
        for event in inventory.trace_events_internal
    )
    assert any(
        event.event_type == "worktree_inspection"
        for event in inspection.trace_events_internal
    )
    assert all(
        event.event_type != "worktree_status"
        for event in inspection.trace_events_internal
    )
    assert "user-path.txt" not in inspection.answer
    assert compute_repo_key(tmp_path) not in inspection.answer
    assert "verification_label=verify" in inspection.answer
    assert "verification_status=succeeded" in inspection.answer
    assert "metadata_present=true" in inspection.answer
    assert "metadata_valid=true" in inspection.answer
