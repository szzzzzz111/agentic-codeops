from pathlib import Path

MAX_FRONTMATTER_LINES = 50
MAX_FRONTMATTER_CHARS = 4096
MAX_SKILL_CONTENT_CHARS = 20000


def load_skill_metadata(repo_path: str) -> list[dict[str, str]]:
    repo_root = _resolve_repo_root(repo_path)
    skills_root = repo_root / ".agents" / "skills"

    if not _is_inside_repo(skills_root.resolve(), repo_root):
        return []
    if not skills_root.is_dir():
        return []

    skills: list[dict[str, str]] = []
    for skill_dir in sorted(
        path for path in skills_root.iterdir() if path.is_dir() and not path.is_symlink()
    ):
        skill_file = (skill_dir / "SKILL.md").resolve()
        if not _is_inside_repo(skill_file, repo_root) or not skill_file.is_file():
            continue

        metadata = _read_frontmatter_metadata(skill_file)
        skills.append(
            {
                "name": metadata["name"],
                "description": metadata["description"],
                "path": _relative_path(skill_file, repo_root),
            }
        )

    return sorted(skills, key=lambda skill: skill["path"])


def load_skill_content(repo_path: str, skill_path: str) -> dict[str, str]:
    repo_root = _resolve_repo_root(repo_path)
    skill_file = _resolve_skill_content_path(repo_root, skill_path)

    content = _read_limited_text(skill_file, MAX_SKILL_CONTENT_CHARS)
    return {
        "path": _relative_path(skill_file, repo_root),
        "content": content,
    }


def _resolve_repo_root(repo_path: str) -> Path:
    repo_root = Path(repo_path).expanduser().resolve()
    if not repo_root.is_dir():
        raise NotADirectoryError(f"仓库路径不是目录：{repo_path}")
    return repo_root


def _resolve_skill_content_path(repo_root: Path, skill_path: str) -> Path:
    relative_path = Path(skill_path)
    if relative_path.is_absolute():
        raise ValueError(f"技能路径不合法：{skill_path}")

    parts = relative_path.parts
    if (
        len(parts) != 4
        or parts[0] != ".agents"
        or parts[1] != "skills"
        or parts[3] != "SKILL.md"
        or parts[2] in {"", ".", ".."}
    ):
        raise ValueError(f"技能路径不合法：{skill_path}")

    skill_file = repo_root.joinpath(*parts)
    if _has_symlink_parent(skill_file, repo_root):
        raise ValueError(f"技能路径不合法：{skill_path}")

    resolved_skill_file = skill_file.resolve()
    if not _is_inside_repo(resolved_skill_file, repo_root):
        raise ValueError(f"技能路径不合法：{skill_path}")
    if not resolved_skill_file.is_file():
        raise FileNotFoundError(f"SKILL.md 不存在：{skill_path}")

    return resolved_skill_file


def _has_symlink_parent(path: Path, repo_root: Path) -> bool:
    current = repo_root
    for part in path.relative_to(repo_root).parts[:-1]:
        current = current / part
        if current.is_symlink():
            return True
    return False


def _read_limited_text(path: Path, max_chars: int) -> str:
    with path.open("r", encoding="utf-8") as file:
        content = file.read(max_chars + 1)

    if len(content) > max_chars:
        raise ValueError("SKILL.md 内容超出读取限制")

    return content


def _read_frontmatter_metadata(skill_file: Path) -> dict[str, str]:
    frontmatter = _read_frontmatter_lines(skill_file)
    metadata: dict[str, str] = {}

    for line in frontmatter:
        stripped_line = line.strip()
        if not stripped_line or stripped_line.startswith("#"):
            continue
        if ":" not in line:
            raise ValueError(f"SKILL.md frontmatter 格式不合法：{stripped_line}")
        key, value = line.split(":", 1)
        key = key.strip()
        if key in {"name", "description"}:
            metadata[key] = _strip_yaml_value(value)

    missing_keys = {"name", "description"} - metadata.keys()
    if missing_keys:
        missing = ", ".join(sorted(missing_keys))
        raise ValueError(f"SKILL.md 缺少必要 metadata：{missing}")

    return metadata


def _read_frontmatter_lines(skill_file: Path) -> list[str]:
    lines: list[str] = []

    with skill_file.open("r", encoding="utf-8") as file:
        first_line = file.readline()
        if first_line.strip() != "---":
            raise ValueError("SKILL.md 缺少 YAML frontmatter")

        total_chars = 0
        for line_number, line in enumerate(file, 1):
            if line.strip() == "---":
                return lines
            total_chars += len(line)
            if (
                line_number > MAX_FRONTMATTER_LINES
                or total_chars > MAX_FRONTMATTER_CHARS
            ):
                raise ValueError("SKILL.md frontmatter 超出读取限制")
            lines.append(line.rstrip("\n"))

    raise ValueError("SKILL.md frontmatter 未闭合")


def _strip_yaml_value(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def _is_inside_repo(path: Path, repo_root: Path) -> bool:
    try:
        path.relative_to(repo_root)
    except ValueError:
        return False
    return True


def _relative_path(path: Path, repo_root: Path) -> str:
    return path.relative_to(repo_root).as_posix()
