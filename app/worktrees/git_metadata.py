from dataclasses import dataclass
import os
from pathlib import Path, PureWindowsPath
import subprocess
import threading
import time
import re


MAX_GIT_METADATA_BYTES = 256_000
GIT_METADATA_TIMEOUT_SECONDS = 10.0
GIT_METADATA_REAP_TIMEOUT_SECONDS = 1.0
GIT_METADATA_READER_JOIN_TIMEOUT_SECONDS = 1.0
_GIT_METADATA_WAIT_POLL_SECONDS = 0.05
_GIT_METADATA_READ_CHUNK_BYTES = 8192
_OBJECT_ID_RE = re.compile(r"[0-9a-fA-F]{40,64}")


@dataclass(frozen=True)
class GitRegistryEntry:
    path: str
    locked: bool


@dataclass
class _MetadataReadState:
    data: bytes | None = None
    oversized: bool = False
    failed: bool = False


def run_git_metadata(
    cwd: Path,
    *args: str,
    timeout: float = GIT_METADATA_TIMEOUT_SECONDS,
    max_bytes: int = MAX_GIT_METADATA_BYTES,
) -> bytes | None:
    env = os.environ.copy()
    env["GIT_OPTIONAL_LOCKS"] = "0"
    try:
        process = subprocess.Popen(
            ["git", *args],
            cwd=cwd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            shell=False,
        )
    except (OSError, subprocess.SubprocessError, ValueError):
        return None
    if process.stdout is None:
        _kill_and_reap(process)
        return None
    state = _MetadataReadState()
    reader = threading.Thread(
        target=_read_metadata_stdout,
        args=(process.stdout, max_bytes, state),
        daemon=True,
        name="git-metadata-reader",
    )
    reader.start()
    return_code = _wait_for_metadata_process(process, state, timeout)
    if return_code is None:
        _kill_and_reap(process)
        _join_reader(reader)
        return None
    _join_reader(reader)
    if reader.is_alive() or state.failed or state.oversized or state.data is None:
        _kill_and_reap(process)
        _join_reader(reader)
        return None
    if return_code != 0:
        _kill_and_reap(process)
        return None
    return state.data


def _wait_for_metadata_process(
    process: subprocess.Popen[bytes],
    state: _MetadataReadState,
    timeout: float,
) -> int | None:
    deadline = time.monotonic() + timeout
    while True:
        if state.failed or state.oversized:
            return None
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return None
        try:
            return process.wait(timeout=min(remaining, _GIT_METADATA_WAIT_POLL_SECONDS))
        except subprocess.TimeoutExpired:
            continue
        except (OSError, subprocess.SubprocessError):
            return None


def _read_metadata_stdout(stdout, max_bytes: int, state: _MetadataReadState) -> None:
    buffer = bytearray()
    try:
        while True:
            remaining = max_bytes - len(buffer)
            read_size = min(_GIT_METADATA_READ_CHUNK_BYTES, remaining + 1)
            chunk = stdout.read(read_size)
            if not chunk:
                state.data = bytes(buffer)
                return
            if len(buffer) + len(chunk) > max_bytes:
                allowed = max_bytes - len(buffer)
                if allowed > 0:
                    buffer.extend(chunk[:allowed])
                state.oversized = True
                return
            buffer.extend(chunk)
    except (OSError, ValueError):
        state.failed = True
    finally:
        try:
            stdout.close()
        except (OSError, ValueError):
            pass


def _kill_and_reap(process: subprocess.Popen[bytes]) -> None:
    try:
        process.kill()
    except (OSError, subprocess.SubprocessError):
        pass
    try:
        process.wait(timeout=GIT_METADATA_REAP_TIMEOUT_SECONDS)
    except (OSError, subprocess.SubprocessError):
        pass


def _join_reader(reader: threading.Thread) -> None:
    reader.join(timeout=GIT_METADATA_READER_JOIN_TIMEOUT_SECONDS)


def git_metadata_text(cwd: Path, *args: str) -> str | None:
    output = run_git_metadata(cwd, *args)
    if output is None:
        return None
    try:
        return output.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return None


def registry_entries(repo_root: Path) -> dict[str, GitRegistryEntry] | None:
    text = git_metadata_text(repo_root, "worktree", "list", "--porcelain", "-z")
    if text is None:
        return None
    records: list[list[str]] = []
    current: list[str] = []
    for token in text.split("\0"):
        if not token:
            continue
        if "\r" in token or "\n" in token:
            return None
        if token.startswith("worktree ") and current:
            records.append(current)
            current = []
        current.append(token)
    if current:
        records.append(current)
    parsed: dict[str, GitRegistryEntry] = {}
    for record in records:
        if len(record) < 2 or not record[0].startswith("worktree "):
            return None
        path = record[0][9:]
        if (
            not path
            or not record[1].startswith("HEAD ")
            or not _OBJECT_ID_RE.fullmatch(record[1][5:])
        ):
            return None
        mode_count = sum(
            field == "detached"
            or field == "bare"
            or field.startswith("branch ")
            for field in record[2:]
        )
        if mode_count != 1:
            return None
        known = all(
            field == "detached"
            or field == "bare"
            or field.startswith(("branch ", "locked", "prunable"))
            for field in record[2:]
        )
        if not known:
            return None
        flags = [field.split(" ", 1)[0] for field in record[2:] if field.startswith(("locked", "prunable"))]
        if len(flags) != len(set(flags)):
            return None
        normalized = normalized_path(Path(path))
        if normalized in parsed:
            return None
        parsed[normalized] = GitRegistryEntry(
            path=normalized,
            locked=any(field == "locked" or field.startswith("locked ") for field in record),
        )
    return parsed


def normalized_path(path: Path) -> str:
    normalized = path.resolve().as_posix()
    return normalized.lower() if PureWindowsPath(normalized).drive else normalized
