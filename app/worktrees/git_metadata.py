from dataclasses import dataclass
import os
from pathlib import Path, PureWindowsPath
import subprocess
import tempfile
import re


MAX_GIT_METADATA_BYTES = 256_000
GIT_METADATA_TIMEOUT_SECONDS = 10.0
_OBJECT_ID_RE = re.compile(r"[0-9a-fA-F]{40,64}")


@dataclass(frozen=True)
class GitRegistryEntry:
    path: str
    locked: bool


def run_git_metadata(
    cwd: Path,
    *args: str,
    timeout: float = GIT_METADATA_TIMEOUT_SECONDS,
    max_bytes: int = MAX_GIT_METADATA_BYTES,
) -> bytes | None:
    env = os.environ.copy()
    env["GIT_OPTIONAL_LOCKS"] = "0"
    try:
        with tempfile.TemporaryFile() as output:
            process = subprocess.Popen(
                ["git", *args],
                cwd=cwd,
                env=env,
                stdout=output,
                stderr=subprocess.DEVNULL,
                shell=False,
            )
            try:
                return_code = process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
                return None
            if return_code != 0 or output.tell() > max_bytes:
                return None
            output.seek(0)
            return output.read(max_bytes + 1)
    except OSError:
        return None


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
