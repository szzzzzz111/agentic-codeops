from pathlib import Path

IGNORED_DIRS = {".git", "__pycache__", ".venv", "node_modules"}
SENSITIVE_NAMES = {
    ".env",
    ".netrc",
    ".npmrc",
    ".pypirc",
    "id_rsa",
    "id_dsa",
    "id_ecdsa",
    "id_ed25519",
}
SENSITIVE_EXTENSIONS = {
    ".key",
    ".pem",
    ".crt",
    ".cer",
    ".der",
    ".p12",
    ".pfx",
}
SENSITIVE_NAME_PARTS = ("secret", "token", "credential", "password", "private")
MAX_BINARY_SAMPLE_BYTES = 2048


def list_files(repo_path: str) -> list[str]:
    repo_root = _resolve_repo_root(repo_path)
    files: list[str] = []

    for path in repo_root.rglob("*"):
        if path.is_dir():
            continue
        if not _is_inside_repo(path.resolve(), repo_root):
            continue
        if _is_ignored_path(path, repo_root):
            continue
        if _is_binary_file(path):
            continue
        files.append(_relative_path(path, repo_root))

    return sorted(files)


def read_file(repo_path: str, file_path: str, max_chars: int = 12000) -> str:
    if max_chars < 1:
        raise ValueError("max_chars 必须大于 0")

    repo_root = _resolve_repo_root(repo_path)
    target_path = _resolve_inside_repo(repo_root, file_path)

    if not target_path.is_file():
        raise FileNotFoundError(f"文件不存在：{file_path}")
    if _is_ignored_path(target_path, repo_root):
        raise ValueError(f"文件不允许访问：{file_path}")
    if _is_binary_file(target_path):
        raise ValueError(f"不允许读取二进制文件：{file_path}")

    return target_path.read_text(encoding="utf-8")[:max_chars]


def search_code(
    repo_path: str,
    keyword: str,
    max_results: int = 20,
) -> list[dict[str, str | int]]:
    if max_results < 1:
        return []
    if not keyword:
        return []

    repo_root = _resolve_repo_root(repo_path)
    results: list[dict[str, str | int]] = []

    for relative_file in list_files(repo_path):
        path = repo_root / relative_file
        lines = path.read_text(encoding="utf-8").splitlines()
        for line_number, line in enumerate(lines, 1):
            if keyword in line:
                results.append(
                    {
                        "file_path": relative_file,
                        "line_number": line_number,
                        "line_text": line.strip(),
                    }
                )
                if len(results) >= max_results:
                    return results

    return results


def _resolve_repo_root(repo_path: str) -> Path:
    repo_root = Path(repo_path).expanduser().resolve()
    if not repo_root.is_dir():
        raise NotADirectoryError(f"仓库路径不是目录：{repo_path}")
    return repo_root


def _resolve_inside_repo(repo_root: Path, file_path: str) -> Path:
    candidate = Path(file_path)
    if not candidate.is_absolute():
        candidate = repo_root / candidate
    resolved = candidate.expanduser().resolve()

    if not _is_inside_repo(resolved, repo_root):
        raise ValueError(f"路径逃逸仓库：{file_path}")

    return resolved


def _is_inside_repo(path: Path, repo_root: Path) -> bool:
    try:
        path.relative_to(repo_root)
    except ValueError:
        return False
    return True


def _relative_path(path: Path, repo_root: Path) -> str:
    return path.relative_to(repo_root).as_posix()


def _is_ignored_path(path: Path, repo_root: Path) -> bool:
    relative_parts = path.relative_to(repo_root).parts
    parent_parts = relative_parts[:-1]
    file_name = path.name

    if any(part in IGNORED_DIRS or _is_hidden(part) for part in parent_parts):
        return True
    return _is_sensitive_file_name(file_name)


def _is_hidden(name: str) -> bool:
    return name.startswith(".")


def _is_sensitive_file_name(file_name: str) -> bool:
    lower_name = file_name.lower()
    suffix = Path(lower_name).suffix

    if lower_name in SENSITIVE_NAMES:
        return True
    if lower_name.startswith(".env"):
        return True
    if suffix in SENSITIVE_EXTENSIONS:
        return True
    return any(part in lower_name for part in SENSITIVE_NAME_PARTS)


def _is_binary_file(path: Path) -> bool:
    try:
        sample = path.read_bytes()[:MAX_BINARY_SAMPLE_BYTES]
    except OSError:
        return True
    if b"\0" in sample:
        return True
    try:
        sample.decode("utf-8")
    except UnicodeDecodeError:
        return True
    return False
