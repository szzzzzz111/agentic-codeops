from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath, PureWindowsPath
import re

from app.tools import file_tools


_HUNK_RE = re.compile(r"^@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@")


@dataclass(frozen=True)
class PatchApplyResult:
    applied: bool
    changed_files: list[str] = field(default_factory=list)
    error: str | None = None


@dataclass(frozen=True)
class _FilePatch:
    file_path: str
    hunks: list[list[str]]


def apply_unified_diff(repo_path: str | Path, diff_text: str) -> PatchApplyResult:
    plan_result = preflight_unified_diff(repo_path, diff_text)
    if not plan_result.applied:
        return plan_result
    try:
        repo_root = Path(repo_path).resolve()
        file_patches = _parse_unified_diff(diff_text)
        planned: dict[Path, str] = {}
        originals: dict[Path, str] = {}
        changed_files: list[str] = []

        for file_patch in file_patches:
            target = _safe_target(repo_root, file_patch.file_path)
            original = target.read_text(encoding="utf-8")
            originals[target] = original
            planned[target] = _apply_file_patch(original, file_patch)
            changed_files.append(file_patch.file_path)
    except ValueError as exc:
        return PatchApplyResult(applied=False, error=str(exc))
    except (OSError, UnicodeDecodeError):
        return PatchApplyResult(applied=False, error="io_error")

    written: list[Path] = []
    try:
        for path, content in planned.items():
            path.write_text(content, encoding="utf-8")
            written.append(path)
    except OSError:
        for path in written:
            try:
                path.write_text(originals[path], encoding="utf-8")
            except OSError:
                pass
        return PatchApplyResult(applied=False, error="io_error")

    return PatchApplyResult(applied=True, changed_files=changed_files)


def preflight_unified_diff(repo_path: str | Path, diff_text: str) -> PatchApplyResult:
    try:
        repo_root = Path(repo_path).resolve()
        file_patches = _parse_unified_diff(diff_text)
        changed_files: list[str] = []

        for file_patch in file_patches:
            target = _safe_target(repo_root, file_patch.file_path)
            original = target.read_text(encoding="utf-8")
            _apply_file_patch(original, file_patch)
            changed_files.append(file_patch.file_path)
    except ValueError as exc:
        return PatchApplyResult(applied=False, error=str(exc))
    except (OSError, UnicodeDecodeError):
        return PatchApplyResult(applied=False, error="io_error")
    return PatchApplyResult(applied=True, changed_files=changed_files)


def _parse_unified_diff(diff_text: str) -> list[_FilePatch]:
    lines = diff_text.splitlines()
    patches: list[_FilePatch] = []
    index = 0
    while index < len(lines):
        if not lines[index].startswith("--- "):
            index += 1
            continue
        old_path = _clean_diff_path(lines[index][4:].strip())
        index += 1
        if index >= len(lines) or not lines[index].startswith("+++ "):
            raise ValueError("invalid_diff")
        new_path = _clean_diff_path(lines[index][4:].strip())
        if old_path != new_path:
            raise ValueError("unsupported_rename")
        index += 1
        hunks: list[list[str]] = []
        while index < len(lines) and not lines[index].startswith("--- "):
            if not lines[index].startswith("@@ "):
                raise ValueError("invalid_diff")
            hunk = [lines[index]]
            index += 1
            while index < len(lines) and not lines[index].startswith("@@ ") and not lines[
                index
            ].startswith("--- "):
                hunk.append(lines[index])
                index += 1
            hunks.append(hunk)
        patches.append(_FilePatch(file_path=new_path, hunks=hunks))
    if not patches:
        raise ValueError("invalid_diff")
    return patches


def _apply_file_patch(original: str, file_patch: _FilePatch) -> str:
    original_lines = original.splitlines(keepends=True)
    output: list[str] = []
    cursor = 0
    for hunk in file_patch.hunks:
        match = _HUNK_RE.match(hunk[0])
        if match is None:
            raise ValueError("invalid_diff")
        old_start = int(match.group(1)) - 1
        if old_start < cursor or old_start > len(original_lines):
            raise ValueError("context_mismatch")
        output.extend(original_lines[cursor:old_start])
        cursor = old_start
        for raw_line in hunk[1:]:
            if not raw_line:
                raise ValueError("invalid_diff")
            marker = raw_line[0]
            content = raw_line[1:] + "\n"
            if marker == " ":
                _require_line(original_lines, cursor, content)
                output.append(original_lines[cursor])
                cursor += 1
            elif marker == "-":
                _require_line(original_lines, cursor, content)
                cursor += 1
            elif marker == "+":
                output.append(content)
            elif raw_line.startswith("\\ No newline"):
                continue
            else:
                raise ValueError("invalid_diff")
    output.extend(original_lines[cursor:])
    return "".join(output)


def _require_line(lines: list[str], index: int, expected: str) -> None:
    if index >= len(lines) or lines[index] != expected:
        raise ValueError("context_mismatch")


def _safe_target(repo_root: Path, file_path: str) -> Path:
    pure = PurePosixPath(file_path)
    if (
        PureWindowsPath(file_path).is_absolute()
        or pure.is_absolute()
        or ".." in pure.parts
    ):
        raise ValueError("unsafe_path")
    target = (repo_root / file_path).resolve()
    try:
        target.relative_to(repo_root)
    except ValueError as exc:
        raise ValueError("unsafe_path") from exc
    if any(part.startswith(".") for part in PurePosixPath(file_path).parts):
        raise ValueError("unsafe_path")
    if not target.is_file():
        raise ValueError("missing_file")
    if file_tools._is_ignored_path(target, repo_root):
        raise ValueError("unsafe_path")
    if file_tools._is_binary_file(target):
        raise ValueError("binary_file")
    return target


def _clean_diff_path(raw_path: str) -> str:
    path = raw_path.split("\t", 1)[0].strip()
    if path.startswith("a/") or path.startswith("b/"):
        return path[2:]
    return path
