from __future__ import annotations

import hashlib
import os
import re
import shutil
import signal
import stat
import subprocess
import threading
import time
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from .contracts import (
    GitSnapshot,
    TrackedIndexEntry,
    TrackedWorktreeFile,
    canonical_sha256,
)

DEFAULT_COMMAND_TIMEOUT_SECONDS = 10.0
DEFAULT_OUTPUT_CAP_BYTES = 4 * 1024 * 1024
PROCESS_READER_GRACE_SECONDS = 0.2
TRACKED_CONTENT_TIMEOUT_SECONDS = 10.0
MAX_TRACKED_CONTENT_BYTES = 128 * 1024 * 1024
_HEAD_RE = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
_ENV_ALLOWLIST = (
    "PATH",
    "SYSTEMROOT",
    "WINDIR",
    "COMSPEC",
    "PATHEXT",
    "TMPDIR",
    "TMP",
    "TEMP",
)
_GIT_OVERRIDES = (
    "-c",
    "core.fsmonitor=false",
    "-c",
    "core.untrackedCache=false",
    "-c",
    "diff.external=",
)


class GitSnapshotCollectionError(RuntimeError):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def _process_isolation_supported() -> bool:
    return (
        os.name == "posix"
        and hasattr(os, "O_NOFOLLOW")
        and hasattr(os, "O_DIRECTORY")
        and os.open in os.supports_dir_fd
    )


@dataclass(frozen=True)
class _Sample:
    repository_id: str
    head: str
    status: bytes
    tracked_diff: bytes
    tracked_changed_paths: tuple[str, ...]
    all_untracked_paths: tuple[str, ...]
    tracked_index_entries: tuple[TrackedIndexEntry, ...]
    tracked_worktree_files: tuple[TrackedWorktreeFile, ...]


def _controlled_git_env() -> dict[str, str]:
    env = {
        key: os.environ[key]
        for key in _ENV_ALLOWLIST
        if key != "PATH" and key in os.environ
    }
    env.update(
        {
            "PATH": os.defpath,
            "LC_ALL": "C",
            "LANG": "C",
            "GIT_OPTIONAL_LOCKS": "0",
            "GIT_TERMINAL_PROMPT": "0",
            "GIT_PAGER": "cat",
            "PAGER": "cat",
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_SYSTEM": os.devnull,
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_ATTR_NOSYSTEM": "1",
            "NoDefaultCurrentDirectoryInExePath": "1",
        }
    )
    return env


def _terminate_process(process: subprocess.Popen[bytes]) -> None:
    if os.name == "posix":
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except (OSError, ProcessLookupError):
            pass
    elif process.poll() is None:
        try:
            process.kill()
        except OSError:
            pass


def _run_bounded_process(
    argv: list[str],
    *,
    cwd: Path,
    env: dict[str, str],
    timeout_seconds: float,
    output_cap_bytes: int,
) -> tuple[bytes, bytes, int]:
    if not _process_isolation_supported():
        raise GitSnapshotCollectionError("PROCESS_ISOLATION_UNAVAILABLE")
    if (
        not argv
        or any(not isinstance(arg, str) or not arg for arg in argv)
        or timeout_seconds <= 0
        or output_cap_bytes <= 0
    ):
        raise GitSnapshotCollectionError("COMMAND_ARGUMENT_INVALID")
    try:
        process = subprocess.Popen(
            argv,
            cwd=cwd,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            start_new_session=True,
            creationflags=0,
        )
    except OSError as exc:
        raise GitSnapshotCollectionError("COMMAND_START_FAILED") from exc

    stdout = bytearray()
    stderr = bytearray()
    output_lock = threading.Lock()
    overflow = threading.Event()
    total_bytes = 0

    def read_stream(stream: object, sink: bytearray) -> None:
        nonlocal total_bytes
        try:
            while True:
                chunk = stream.read(65536)  # type: ignore[attr-defined]
                if not chunk:
                    break
                with output_lock:
                    remaining = max(0, output_cap_bytes - total_bytes)
                    if remaining:
                        sink.extend(chunk[:remaining])
                    total_bytes += len(chunk)
                    if total_bytes > output_cap_bytes:
                        overflow.set()
        except OSError:
            overflow.set()

    assert process.stdout is not None
    assert process.stderr is not None
    readers = (
        threading.Thread(target=read_stream, args=(process.stdout, stdout), daemon=True),
        threading.Thread(target=read_stream, args=(process.stderr, stderr), daemon=True),
    )
    for reader in readers:
        reader.start()

    deadline = time.monotonic() + timeout_seconds
    error_code: str | None = None
    while process.poll() is None:
        if overflow.is_set():
            error_code = "COMMAND_OUTPUT_LIMIT_EXCEEDED"
            break
        if time.monotonic() >= deadline:
            error_code = "COMMAND_TIMED_OUT"
            break
        try:
            process.wait(timeout=min(0.05, max(0.001, deadline - time.monotonic())))
        except subprocess.TimeoutExpired:
            pass
    if overflow.is_set() and error_code is None:
        error_code = "COMMAND_OUTPUT_LIMIT_EXCEEDED"
    if error_code is not None:
        _terminate_process(process)
    try:
        process.wait(timeout=1.0)
    except subprocess.TimeoutExpired:
        _terminate_process(process)
        try:
            process.wait(timeout=1.0)
        except subprocess.TimeoutExpired as exc:
            raise GitSnapshotCollectionError("PROCESS_CLEANUP_FAILED") from exc
    for reader in readers:
        reader.join(timeout=PROCESS_READER_GRACE_SECONDS)
    lingering_process_tree = any(reader.is_alive() for reader in readers)
    if lingering_process_tree:
        _terminate_process(process)
        for reader in readers:
            reader.join(timeout=1.0)
    process.stdout.close()
    process.stderr.close()
    if any(reader.is_alive() for reader in readers):
        raise GitSnapshotCollectionError("PROCESS_CLEANUP_FAILED")
    if error_code is not None:
        raise GitSnapshotCollectionError(error_code)
    if lingering_process_tree:
        raise GitSnapshotCollectionError("COMMAND_PROCESS_TREE_REMAINED")
    if overflow.is_set():
        raise GitSnapshotCollectionError("COMMAND_OUTPUT_LIMIT_EXCEEDED")
    return bytes(stdout), bytes(stderr), int(process.returncode)


def _resolve_git_executable(cwd: Path) -> str:
    executable = shutil.which("git", path=os.defpath)
    if executable is None:
        raise GitSnapshotCollectionError("GIT_UNAVAILABLE")
    try:
        resolved = Path(executable).resolve(strict=True)
        mode = os.stat(resolved).st_mode
    except OSError as exc:
        raise GitSnapshotCollectionError("GIT_EXECUTABLE_UNTRUSTED") from exc
    if (
        not resolved.is_absolute()
        or not stat.S_ISREG(mode)
        or not os.access(resolved, os.X_OK)
        or resolved.is_relative_to(cwd)
    ):
        raise GitSnapshotCollectionError("GIT_EXECUTABLE_UNTRUSTED")
    return os.fspath(resolved)


def _run_git_command(
    cwd: Path,
    args: tuple[str, ...],
    *,
    git_executable: str | None = None,
    allowed_returncodes: tuple[int, ...] = (0,),
) -> tuple[bytes, int]:
    env = _controlled_git_env()
    executable = git_executable or _resolve_git_executable(cwd)
    argv = [executable, *_GIT_OVERRIDES, *args]
    stdout, _stderr, returncode = _run_bounded_process(
        argv,
        cwd=cwd,
        env=env,
        timeout_seconds=DEFAULT_COMMAND_TIMEOUT_SECONDS,
        output_cap_bytes=DEFAULT_OUTPUT_CAP_BYTES,
    )
    if returncode not in allowed_returncodes:
        raise GitSnapshotCollectionError("GIT_COMMAND_FAILED")
    return stdout, returncode


def _decode_line(value: bytes, error_code: str) -> str:
    try:
        text = value.decode("utf-8", errors="strict").strip()
    except UnicodeDecodeError as exc:
        raise GitSnapshotCollectionError(error_code) from exc
    if not text or "\x00" in text or "\n" in text or "\r" in text:
        raise GitSnapshotCollectionError(error_code)
    return text


def _validate_repo_path(path: str) -> str:
    if not path or "\\" in path or path.startswith("/") or path.endswith("/"):
        raise GitSnapshotCollectionError("MALFORMED_NUL_PATH_OUTPUT")
    parts = path.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise GitSnapshotCollectionError("MALFORMED_NUL_PATH_OUTPUT")
    if PurePosixPath(path).as_posix() != path:
        raise GitSnapshotCollectionError("MALFORMED_NUL_PATH_OUTPUT")
    return path


def _parse_nul_paths(value: bytes) -> tuple[str, ...]:
    if not value:
        return ()
    if not value.endswith(b"\0"):
        raise GitSnapshotCollectionError("MALFORMED_NUL_PATH_OUTPUT")
    records = value[:-1].split(b"\0")
    if any(not record for record in records):
        raise GitSnapshotCollectionError("MALFORMED_NUL_PATH_OUTPUT")
    try:
        paths = tuple(_validate_repo_path(record.decode("utf-8", "strict")) for record in records)
    except UnicodeDecodeError as exc:
        raise GitSnapshotCollectionError("MALFORMED_NUL_PATH_OUTPUT") from exc
    if len(paths) != len(set(paths)):
        raise GitSnapshotCollectionError("MALFORMED_NUL_PATH_OUTPUT")
    return tuple(sorted(paths))


def _parse_tracked_index(value: bytes) -> tuple[TrackedIndexEntry, ...]:
    if value and not value.endswith(b"\0"):
        raise GitSnapshotCollectionError("MALFORMED_TRACKED_INVENTORY")
    records = value[:-1].split(b"\0") if value else []
    entries: list[TrackedIndexEntry] = []
    for record in records:
        try:
            metadata, path_bytes = record.split(b"\t", 1)
            mode, object_id, stage = metadata.decode("ascii").split(" ")
            path = path_bytes.decode("utf-8", "strict")
        except (UnicodeDecodeError, ValueError) as exc:
            raise GitSnapshotCollectionError("MALFORMED_TRACKED_INVENTORY") from exc
        path = _validate_repo_path(path)
        if not _HEAD_RE.fullmatch(object_id) or stage != "0":
            raise GitSnapshotCollectionError("MALFORMED_TRACKED_INVENTORY")
        if mode == "120000":
            raise GitSnapshotCollectionError("TRACKED_SYMLINK_NOT_SUPPORTED")
        if mode == "160000":
            raise GitSnapshotCollectionError("GITLINK_NOT_SUPPORTED")
        if not re.fullmatch(r"10[0-7]{4}", mode):
            raise GitSnapshotCollectionError("MALFORMED_TRACKED_INVENTORY")
        entries.append(TrackedIndexEntry(path=path, mode=mode, object_id=object_id))
    paths = [entry.path for entry in entries]
    if len(paths) != len(set(paths)):
        raise GitSnapshotCollectionError("MALFORMED_TRACKED_INVENTORY")
    return tuple(sorted(entries, key=lambda entry: entry.path))


def _preflight_worktree_paths(cwd: Path, tracked_paths: tuple[str, ...]) -> None:
    for relative in tracked_paths:
        candidate = cwd
        parts = relative.split("/")
        for index, part in enumerate(parts):
            candidate = candidate / part
            try:
                mode = os.lstat(candidate).st_mode
            except FileNotFoundError:
                break
            except OSError as exc:
                raise GitSnapshotCollectionError(
                    "TRACKED_PATH_INSPECTION_FAILED"
                ) from exc
            if stat.S_ISLNK(mode):
                raise GitSnapshotCollectionError(
                    "TRACKED_WORKTREE_SYMLINK_NOT_SUPPORTED"
                )
            if index < len(parts) - 1 and not stat.S_ISDIR(mode):
                raise GitSnapshotCollectionError("TRACKED_WORKTREE_PATH_UNSAFE")
            if index == len(parts) - 1 and not stat.S_ISREG(mode):
                raise GitSnapshotCollectionError("TRACKED_WORKTREE_PATH_UNSAFE")


def _repository_identity(cwd: Path, git_executable: str) -> str:
    try:
        root_raw, _ = _run_git_command(
            cwd,
            ("rev-parse", "--show-toplevel"),
            git_executable=git_executable,
        )
    except GitSnapshotCollectionError as exc:
        if exc.code == "GIT_COMMAND_FAILED":
            raise GitSnapshotCollectionError("NOT_A_GIT_REPOSITORY") from exc
        raise
    root_text = _decode_line(root_raw, "NOT_A_GIT_REPOSITORY")
    try:
        root = Path(root_text).resolve(strict=True)
    except OSError as exc:
        raise GitSnapshotCollectionError("NOT_A_GIT_REPOSITORY") from exc
    if root != cwd:
        raise GitSnapshotCollectionError("REPOSITORY_ROOT_MISMATCH")
    common_raw, _ = _run_git_command(
        cwd,
        ("rev-parse", "--git-common-dir"),
        git_executable=git_executable,
    )
    common_text = _decode_line(common_raw, "GIT_COMMON_DIR_INVALID")
    common_input = Path(common_text)
    if not common_input.is_absolute():
        common_input = cwd / common_input
    try:
        common = common_input.resolve(strict=True)
    except OSError as exc:
        raise GitSnapshotCollectionError("GIT_COMMON_DIR_INVALID") from exc
    return canonical_sha256(
        {"repository_root": cwd.as_posix(), "git_common_dir": common.as_posix()}
    )


def _read_head(cwd: Path, git_executable: str) -> str:
    raw, _ = _run_git_command(
        cwd,
        ("rev-parse", "--verify", "HEAD"),
        git_executable=git_executable,
    )
    head = _decode_line(raw, "HEAD_NOT_OBSERVED")
    if not _HEAD_RE.fullmatch(head):
        raise GitSnapshotCollectionError("HEAD_NOT_OBSERVED")
    return head


def _hash_tracked_worktree_files(
    cwd: Path,
    tracked_paths: tuple[str, ...],
) -> tuple[TrackedWorktreeFile, ...]:
    deadline = time.monotonic() + TRACKED_CONTENT_TIMEOUT_SECONDS
    total_bytes = 0
    states: list[TrackedWorktreeFile] = []
    for relative in tracked_paths:
        try:
            descriptor = _open_tracked_file(cwd, relative)
        except FileNotFoundError:
            continue
        except OSError as exc:
            raise GitSnapshotCollectionError("TRACKED_PATH_INSPECTION_FAILED") from exc
        digest = canonical_sha256(b"")
        try:
            file_stat = os.fstat(descriptor)
            if not stat.S_ISREG(file_stat.st_mode):
                raise GitSnapshotCollectionError("TRACKED_WORKTREE_PATH_UNSAFE")
            hasher = hashlib.sha256()
            while True:
                if time.monotonic() >= deadline:
                    raise GitSnapshotCollectionError(
                        "TRACKED_CONTENT_READ_TIMED_OUT"
                    )
                chunk = os.read(descriptor, 65536)
                if not chunk:
                    break
                total_bytes += len(chunk)
                if total_bytes > MAX_TRACKED_CONTENT_BYTES:
                    raise GitSnapshotCollectionError(
                        "TRACKED_CONTENT_LIMIT_EXCEEDED"
                    )
                hasher.update(chunk)
            digest = hasher.hexdigest()
            mode = f"{stat.S_IFREG | stat.S_IMODE(file_stat.st_mode):06o}"
        finally:
            os.close(descriptor)
        states.append(
            TrackedWorktreeFile(path=relative, mode=mode, content_sha256=digest)
        )
    return tuple(states)


def _open_tracked_file(cwd: Path, relative: str) -> int:
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    directory_flags = (
        os.O_RDONLY | os.O_CLOEXEC | os.O_DIRECTORY | os.O_NONBLOCK | nofollow
    )
    directory = os.open(cwd, directory_flags)
    try:
        parts = relative.split("/")
        for part in parts[:-1]:
            next_directory = os.open(part, directory_flags, dir_fd=directory)
            os.close(directory)
            directory = next_directory
        return os.open(
            parts[-1],
            os.O_RDONLY | os.O_CLOEXEC | os.O_NONBLOCK | nofollow,
            dir_fd=directory,
        )
    finally:
        os.close(directory)


def _collect_sample(cwd: Path, git_executable: str) -> _Sample:
    repository_id = _repository_identity(cwd, git_executable)
    start_head = _read_head(cwd, git_executable)
    tracked_index_raw, _ = _run_git_command(
        cwd,
        ("ls-files", "--stage", "-z"),
        git_executable=git_executable,
    )
    tracked_index_entries = _parse_tracked_index(tracked_index_raw)
    tracked_paths = tuple(entry.path for entry in tracked_index_entries)
    _preflight_worktree_paths(cwd, tracked_paths)
    filter_config, _ = _run_git_command(
        cwd,
        (
            "config",
            "--includes",
            "--null",
            "--get-regexp",
            r"^filter\..*\.(clean|process)$",
        ),
        git_executable=git_executable,
        allowed_returncodes=(0, 1),
    )
    if filter_config:
        raise GitSnapshotCollectionError("CONTENT_FILTER_NOT_SUPPORTED")
    tracked_worktree_files = _hash_tracked_worktree_files(cwd, tracked_paths)
    status, _ = _run_git_command(
        cwd,
        (
            "status",
            "--porcelain=v1",
            "-z",
            "--untracked-files=all",
            "--ignored=matching",
        ),
        git_executable=git_executable,
    )
    tracked_diff, _ = _run_git_command(
        cwd,
        ("diff", "--binary", "--no-ext-diff", "--no-textconv", "HEAD", "--"),
        git_executable=git_executable,
    )
    tracked_paths_raw, _ = _run_git_command(
        cwd,
        (
            "diff",
            "--name-only",
            "-z",
            "--no-renames",
            "--no-ext-diff",
            "--no-textconv",
            "HEAD",
            "--",
        ),
        git_executable=git_executable,
    )
    untracked_raw, _ = _run_git_command(
        cwd,
        ("ls-files", "--others", "-z"),
        git_executable=git_executable,
    )
    end_head = _read_head(cwd, git_executable)
    if start_head != end_head:
        raise GitSnapshotCollectionError("REPOSITORY_CHANGED_DURING_COLLECTION")
    tracked_paths = _parse_nul_paths(tracked_paths_raw)
    untracked_paths = _parse_nul_paths(untracked_raw)
    clean = not status
    evidence_clean = not tracked_diff and not tracked_paths and not untracked_paths
    if clean != evidence_clean:
        raise GitSnapshotCollectionError("INCONSISTENT_GIT_SNAPSHOT")
    return _Sample(
        repository_id=repository_id,
        head=start_head,
        status=status,
        tracked_diff=tracked_diff,
        tracked_changed_paths=tracked_paths,
        all_untracked_paths=untracked_paths,
        tracked_index_entries=tracked_index_entries,
        tracked_worktree_files=tracked_worktree_files,
    )


def _validated_input_root(repo_path: str | Path) -> Path:
    supplied = Path(repo_path)
    if ".." in supplied.parts:
        raise GitSnapshotCollectionError("REPOSITORY_PATH_TRAVERSAL")
    absolute = Path(os.path.abspath(os.fspath(supplied)))
    try:
        resolved = absolute.resolve(strict=True)
    except OSError as exc:
        raise GitSnapshotCollectionError("REPOSITORY_PATH_UNAVAILABLE") from exc
    if absolute != resolved:
        raise GitSnapshotCollectionError("SYMLINK_TRAVERSAL")
    if not resolved.is_dir():
        raise GitSnapshotCollectionError("REPOSITORY_PATH_UNAVAILABLE")
    return resolved


def collect_git_snapshot(repo_path: str | Path) -> GitSnapshot:
    if not _process_isolation_supported():
        raise GitSnapshotCollectionError("PROCESS_ISOLATION_UNAVAILABLE")
    cwd = _validated_input_root(repo_path)
    git_executable = _resolve_git_executable(cwd)
    first = _collect_sample(cwd, git_executable)
    second = _collect_sample(cwd, git_executable)
    if first != second:
        raise GitSnapshotCollectionError("REPOSITORY_CHANGED_DURING_COLLECTION")
    clean = not first.status
    return GitSnapshot(
        repository_id=first.repository_id,
        head=first.head,
        status_sha256=canonical_sha256(first.status),
        tracked_diff_sha256=canonical_sha256(first.tracked_diff),
        tracked_changed_paths=first.tracked_changed_paths,
        all_untracked_paths=first.all_untracked_paths,
        tracked_index_entries=first.tracked_index_entries,
        tracked_worktree_files=first.tracked_worktree_files,
        clean=clean,
        stability_samples=2,
    )
