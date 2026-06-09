from dataclasses import dataclass
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import subprocess

from app.tools import file_tools
from app.worktrees.store import WorktreeRecord


MAX_METADATA_BYTES = 256_000
MAX_PREVIEW_FILES = 20
MAX_PREVIEW_CHARS = 6000
MAX_FILE_LINES = 80
MAX_LINE_CHARS = 300
STREAM_CHUNK_BYTES = 64_000
MAX_RAW_LINE_BYTES = 4096
MAX_PUBLIC_FIELD_CHARS = 120
MAX_PUBLIC_PATH_CHARS = 300
MAX_PUBLIC_CHANGED_FILES = 20

_WINDOWS_PATH_RE = re.compile(r"\b[A-Za-z]:[\\/][^\s,;'\")\]]+")
_POSIX_PATH_RE = re.compile(
    r"(?<![\w.])/(?:Users|home|root|tmp|var|etc|opt|mnt|srv)/[^\s,;'\")\]]+"
)
_REPOPILOT_PATH_RE = re.compile(r"\.repopilot[\\/][^\s,;'\")\]]+")
_SECRET_RE = re.compile(
    r"\b[A-Za-z0-9_]*(?:API_KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL)"
    r"\s*=\s*(?:\"[^\"]*\"|'[^']*'|[^\s,;]+)",
    re.IGNORECASE,
)
_OBJECT_ID_RE = re.compile(r"[0-9a-fA-F]{40,64}")


@dataclass(frozen=True)
class WorktreeInspectionResult:
    found: bool
    record: WorktreeRecord | None = None
    metadata_valid: bool = False
    directory_present: bool = False
    git_registry_present: bool = False
    registry_path_matches_expected: bool = False
    head_matches_base_commit: bool = False
    changed_files: list[str] | None = None
    additions: int = 0
    deletions: int = 0
    binary_files: int = 0
    hunk_count: int = 0
    untracked_count: int = 0
    preview: str = ""
    omitted_files: int = 0
    truncated_files: int = 0
    truncated_lines: int = 0
    truncated_chars: int = 0
    partial: bool = False


def inspect_worktree(
    *,
    repo_root: Path,
    record: WorktreeRecord,
) -> WorktreeInspectionResult:
    managed_root = (repo_root / ".repopilot" / "worktrees").resolve()
    expected = (managed_root / record.worktree_id).resolve()
    if not _is_within(expected, managed_root) or not _OBJECT_ID_RE.fullmatch(
        record.base_commit
    ):
        return WorktreeInspectionResult(
            found=True,
            record=record,
            partial=True,
            changed_files=[],
        )
    directory_present = expected.is_dir()
    registry_paths, registry_partial = _registry_paths(repo_root)
    normalized_expected = _normalized_path(expected)
    git_registry_present = normalized_expected in registry_paths
    if not directory_present:
        return WorktreeInspectionResult(
            found=True,
            record=record,
            metadata_valid=True,
            directory_present=False,
            git_registry_present=git_registry_present,
            registry_path_matches_expected=git_registry_present,
            partial=registry_partial,
            changed_files=[],
        )

    head = _bounded_git_text(expected, "rev-parse", "HEAD")
    head_matches = head is not None and head.strip() == record.base_commit
    changed_files, paths_partial = _nul_paths(
        expected,
        "diff",
        "--name-only",
        "-z",
        "--no-ext-diff",
        "--no-textconv",
        record.base_commit,
        "--",
    )
    additions, deletions, binary_files, stat_partial = _numstat(
        expected,
        record.base_commit,
    )
    hunk_count, hunk_partial = _stream_hunk_count(expected, record.base_commit)
    untracked_count, untracked_partial = _untracked_count(expected)
    preview, omitted, truncated_files, truncated_lines, truncated_chars, preview_partial = (
        _format_preview(expected, record.base_commit, changed_files)
    )
    return WorktreeInspectionResult(
        found=True,
        record=record,
        metadata_valid=True,
        directory_present=True,
        git_registry_present=git_registry_present,
        registry_path_matches_expected=git_registry_present,
        head_matches_base_commit=head_matches,
        changed_files=changed_files,
        additions=additions,
        deletions=deletions,
        binary_files=binary_files,
        hunk_count=hunk_count,
        untracked_count=untracked_count,
        preview=preview,
        omitted_files=omitted,
        truncated_files=truncated_files,
        truncated_lines=truncated_lines,
        truncated_chars=truncated_chars,
        partial=any(
            (
                registry_partial,
                paths_partial,
                stat_partial,
                hunk_partial,
                untracked_partial,
                preview_partial,
            )
        ),
    )


def safe_public_value(value: str, max_chars: int = MAX_PUBLIC_FIELD_CHARS) -> str:
    normalized = " ".join(str(value).split())
    redacted = _redact(normalized)
    if len(redacted) <= max_chars:
        return redacted or "none"
    return redacted[:max_chars] + "..."


def format_public_changed_files(paths: list[str]) -> tuple[str, int]:
    visible = [
        safe_public_value(path, MAX_PUBLIC_PATH_CHARS)
        for path in paths[:MAX_PUBLIC_CHANGED_FILES]
    ]
    return ", ".join(visible) or "none", max(0, len(paths) - len(visible))


def _registry_paths(repo_root: Path) -> tuple[set[str], bool]:
    text = _bounded_git_text(repo_root, "worktree", "list", "--porcelain", "-z")
    if text is None:
        return set(), True
    paths: set[str] = set()
    for token in text.split("\0"):
        for line in token.splitlines():
            if line.startswith("worktree "):
                paths.add(_normalized_path(Path(line[9:])))
    return paths, False


def _nul_paths(cwd: Path, *args: str) -> tuple[list[str], bool]:
    output = _bounded_git_bytes(cwd, *args)
    if output is None:
        return [], True
    paths = [
        item.decode("utf-8", errors="replace")
        for item in output.split(b"\0")
        if item
    ]
    return paths, False


def _numstat(cwd: Path, base_commit: str) -> tuple[int, int, int, bool]:
    output = _bounded_git_bytes(
        cwd,
        "diff",
        "--numstat",
        "-z",
        "--no-ext-diff",
        "--no-textconv",
        base_commit,
        "--",
    )
    if output is None:
        return 0, 0, 0, True
    additions = deletions = binary_files = 0
    for entry in output.split(b"\0"):
        if not entry:
            continue
        parts = entry.split(b"\t", 2)
        if len(parts) != 3:
            continue
        if parts[0] == b"-" or parts[1] == b"-":
            binary_files += 1
            continue
        try:
            additions += int(parts[0])
            deletions += int(parts[1])
        except ValueError:
            continue
    return additions, deletions, binary_files, False


def _stream_hunk_count(cwd: Path, base_commit: str) -> tuple[int, bool]:
    process = _popen_git(
        cwd,
        "diff",
        "--unified=0",
        "--no-ext-diff",
        "--no-textconv",
        base_commit,
        "--",
    )
    count = 0
    assert process.stdout is not None
    for raw_line, _ in _iter_bounded_lines(process.stdout):
        if raw_line.startswith(b"@@ "):
            count += 1
    return count, process.wait() != 0


def _untracked_count(cwd: Path) -> tuple[int, bool]:
    output = _bounded_git_bytes(
        cwd,
        "status",
        "--porcelain=v1",
        "-z",
        "--untracked-files=all",
    )
    if output is None:
        return 0, True
    return sum(1 for item in output.split(b"\0") if item.startswith(b"?? ")), False


def _format_preview(
    cwd: Path,
    base_commit: str,
    git_paths: list[str],
) -> tuple[str, int, int, int, int, bool]:
    output: list[str] = []
    used_chars = 0
    omitted_files = truncated_files = truncated_lines = truncated_chars = 0
    partial = False
    safe_paths: list[str] = []
    for path in git_paths:
        if len(safe_paths) >= MAX_PREVIEW_FILES:
            omitted_files += 1
            continue
        if not _safe_preview_path(cwd, path):
            omitted_files += 1
            continue
        safe_paths.append(path)

    for path in safe_paths:
        file_output: list[str] = []
        file_used_chars = 0
        file_truncated_lines = 0
        file_truncated_chars = 0
        process = _popen_git(
            cwd,
            "diff",
            "--no-ext-diff",
            "--no-textconv",
            base_commit,
            "--",
            path,
        )
        file_lines = 0
        file_truncated = False
        assert process.stdout is not None
        for raw_line, raw_truncated_bytes in _iter_bounded_lines(process.stdout):
            line = raw_line.decode("utf-8", errors="replace").rstrip("\r\n")
            line = _redact(line)
            file_truncated_chars += raw_truncated_bytes
            if raw_truncated_bytes:
                file_truncated = True
            if len(line) > MAX_LINE_CHARS:
                file_truncated_chars += len(line) - MAX_LINE_CHARS
                line = line[:MAX_LINE_CHARS]
            rendered = line + "\n"
            if file_lines >= MAX_FILE_LINES:
                file_truncated_lines += 1
                file_truncated = True
                continue
            if used_chars + file_used_chars + len(rendered) > MAX_PREVIEW_CHARS:
                remaining = MAX_PREVIEW_CHARS - used_chars - file_used_chars
                if remaining > 0:
                    file_output.append(rendered[:remaining])
                    file_truncated_chars += len(rendered) - remaining
                    file_used_chars += remaining
                else:
                    file_truncated_chars += len(rendered)
                file_truncated = True
                continue
            file_output.append(rendered)
            file_used_chars += len(rendered)
            file_lines += 1
        if process.wait() != 0:
            omitted_files += 1
            partial = True
            continue
        output.extend(file_output)
        used_chars += file_used_chars
        truncated_lines += file_truncated_lines
        truncated_chars += file_truncated_chars
        if file_truncated:
            truncated_files += 1
    return (
        "".join(output).rstrip(),
        omitted_files,
        truncated_files,
        truncated_lines,
        truncated_chars,
        partial,
    )


def _safe_preview_path(repo_root: Path, path: str) -> bool:
    pure = PurePosixPath(path)
    if PureWindowsPath(path).is_absolute() or pure.is_absolute() or ".." in pure.parts:
        return False
    if any(part.startswith(".") for part in pure.parts):
        return False
    target = (repo_root / path).resolve()
    if not _is_within(target, repo_root.resolve()):
        return False
    return (
        target.is_file()
        and not file_tools._is_ignored_path(target, repo_root.resolve())
        and not file_tools._is_binary_file(target)
    )


def _redact(line: str) -> str:
    line = _SECRET_RE.sub("<redacted-secret>", line)
    line = _REPOPILOT_PATH_RE.sub("<state-path>", line)
    line = _WINDOWS_PATH_RE.sub("<local-path>", line)
    return _POSIX_PATH_RE.sub("<local-path>", line)


def _bounded_git_text(cwd: Path, *args: str) -> str | None:
    output = _bounded_git_bytes(cwd, *args)
    return None if output is None else output.decode("utf-8", errors="replace")


def _bounded_git_bytes(cwd: Path, *args: str) -> bytes | None:
    process = _popen_git(cwd, *args)
    assert process.stdout is not None
    output = process.stdout.read(MAX_METADATA_BYTES + 1)
    exceeded = len(output) > MAX_METADATA_BYTES
    _drain_stream(process.stdout)
    return_code = process.wait()
    if exceeded or return_code != 0:
        return None
    return output


def _popen_git(cwd: Path, *args: str) -> subprocess.Popen[bytes]:
    env = os.environ.copy()
    env["GIT_OPTIONAL_LOCKS"] = "0"
    return subprocess.Popen(
        ["git", *args],
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        shell=False,
    )


def _normalized_path(path: Path) -> str:
    normalized = path.resolve().as_posix()
    return normalized.lower() if PureWindowsPath(normalized).drive else normalized


def _iter_bounded_lines(stream):
    while True:
        chunk = stream.readline(MAX_RAW_LINE_BYTES + 1)
        if not chunk:
            return
        kept = chunk[:MAX_RAW_LINE_BYTES]
        omitted = max(0, len(chunk) - len(kept))
        while chunk and not chunk.endswith(b"\n"):
            chunk = stream.readline(MAX_RAW_LINE_BYTES + 1)
            omitted += len(chunk)
        yield kept, omitted


def _drain_stream(stream) -> None:
    while stream.read(STREAM_CHUNK_BYTES):
        pass


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True
