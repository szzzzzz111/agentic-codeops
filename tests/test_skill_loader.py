from pathlib import Path

import pytest

from app.tools.skill_loader import (
    MAX_SKILL_CONTENT_CHARS,
    load_skill_content,
    load_skill_metadata,
)


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_load_skill_metadata_returns_name_description_and_path(
    tmp_path: Path,
) -> None:
    write_text(
        tmp_path / ".agents" / "skills" / "review" / "SKILL.md",
        "---\n"
        "name: review\n"
        "description: 检查代码变更风险。\n"
        "---\n"
        "\n"
        "# Review\n",
    )

    assert load_skill_metadata(str(tmp_path)) == [
        {
            "name": "review",
            "description": "检查代码变更风险。",
            "path": ".agents/skills/review/SKILL.md",
        }
    ]


def test_load_skill_metadata_returns_empty_list_without_skills_dir(
    tmp_path: Path,
) -> None:
    assert load_skill_metadata(str(tmp_path)) == []


def test_load_skill_metadata_returns_stable_order_by_path(tmp_path: Path) -> None:
    write_text(
        tmp_path / ".agents" / "skills" / "zeta" / "SKILL.md",
        "---\nname: zeta\ndescription: 最后一个技能。\n---\n",
    )
    write_text(
        tmp_path / ".agents" / "skills" / "alpha" / "SKILL.md",
        "---\nname: alpha\ndescription: 第一个技能。\n---\n",
    )

    assert load_skill_metadata(str(tmp_path)) == [
        {
            "name": "alpha",
            "description": "第一个技能。",
            "path": ".agents/skills/alpha/SKILL.md",
        },
        {
            "name": "zeta",
            "description": "最后一个技能。",
            "path": ".agents/skills/zeta/SKILL.md",
        },
    ]


def test_load_skill_metadata_does_not_return_full_skill_body(
    tmp_path: Path,
) -> None:
    body_token = "FULL_SKILL_BODY_SHOULD_NOT_LEAK"
    write_text(
        tmp_path / ".agents" / "skills" / "safe" / "SKILL.md",
        "---\n"
        "name: safe\n"
        "description: 只返回元数据。\n"
        "---\n"
        f"\n# Body\n{body_token}\n",
    )

    [metadata] = load_skill_metadata(str(tmp_path))

    assert body_token not in str(metadata)


def test_load_skill_metadata_does_not_return_absolute_paths(tmp_path: Path) -> None:
    write_text(
        tmp_path / ".agents" / "skills" / "paths" / "SKILL.md",
        "---\nname: paths\ndescription: 检查路径格式。\n---\n",
    )

    [metadata] = load_skill_metadata(str(tmp_path))

    assert metadata["path"] == ".agents/skills/paths/SKILL.md"
    assert str(tmp_path) not in metadata["path"]


def test_load_skill_metadata_rejects_missing_required_metadata(
    tmp_path: Path,
) -> None:
    write_text(
        tmp_path / ".agents" / "skills" / "broken" / "SKILL.md",
        "---\nname: broken\n---\n",
    )

    with pytest.raises(ValueError, match="description"):
        load_skill_metadata(str(tmp_path))


def test_load_skill_metadata_rejects_invalid_frontmatter_line(
    tmp_path: Path,
) -> None:
    write_text(
        tmp_path / ".agents" / "skills" / "broken" / "SKILL.md",
        "---\n"
        "name: broken\n"
        "this line is invalid\n"
        "description: 包含非法 frontmatter 行。\n"
        "---\n",
    )

    with pytest.raises(ValueError, match="格式不合法"):
        load_skill_metadata(str(tmp_path))


def test_load_skill_metadata_limits_unclosed_frontmatter_read(
    tmp_path: Path,
) -> None:
    write_text(
        tmp_path / ".agents" / "skills" / "broken" / "SKILL.md",
        "---\n"
        "name: broken\n"
        "description: frontmatter 没有闭合。\n"
        + "body-like-line\n" * 60,
    )

    with pytest.raises(ValueError, match="读取限制"):
        load_skill_metadata(str(tmp_path))


def test_load_skill_content_returns_path_and_full_content(tmp_path: Path) -> None:
    content = (
        "---\n"
        "name: review\n"
        "description: 检查代码变更风险。\n"
        "---\n"
        "\n"
        "# Review\n"
        "Use this skill during review.\n"
    )
    write_text(tmp_path / ".agents" / "skills" / "review" / "SKILL.md", content)

    result = load_skill_content(
        str(tmp_path),
        ".agents/skills/review/SKILL.md",
    )

    assert result == {
        "path": ".agents/skills/review/SKILL.md",
        "content": content,
    }


def test_load_skill_content_does_not_return_absolute_paths(tmp_path: Path) -> None:
    write_text(
        tmp_path / ".agents" / "skills" / "paths" / "SKILL.md",
        "not parsed as metadata\n",
    )

    result = load_skill_content(str(tmp_path), ".agents/skills/paths/SKILL.md")

    assert result["path"] == ".agents/skills/paths/SKILL.md"
    assert str(tmp_path) not in result["path"]
    assert str(tmp_path) not in str(result)


def test_load_skill_content_rejects_path_escape(tmp_path: Path) -> None:
    outside = tmp_path.parent / "outside-skill.md"
    outside.write_text("outside\n", encoding="utf-8")

    with pytest.raises(ValueError, match="技能路径"):
        load_skill_content(str(tmp_path), "../outside-skill.md")


def test_load_skill_content_rejects_non_skill_files(tmp_path: Path) -> None:
    write_text(tmp_path / "README.md", "repo readme\n")
    write_text(tmp_path / ".agents" / "skills" / "review" / "notes.md", "notes\n")

    with pytest.raises(ValueError, match="技能路径"):
        load_skill_content(str(tmp_path), "README.md")

    with pytest.raises(ValueError, match="技能路径"):
        load_skill_content(str(tmp_path), ".agents/skills/review/notes.md")


def test_load_skill_content_rejects_missing_skill_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="SKILL.md"):
        load_skill_content(str(tmp_path), ".agents/skills/missing/SKILL.md")


def test_load_skill_content_rejects_symlink_skill_directory(tmp_path: Path) -> None:
    real_dir = tmp_path / "real-skill"
    real_dir.mkdir()
    write_text(real_dir / "SKILL.md", "linked content\n")
    link_dir = tmp_path / ".agents" / "skills" / "linked"
    link_dir.parent.mkdir(parents=True)
    try:
        link_dir.symlink_to(real_dir, target_is_directory=True)
    except OSError:
        pytest.skip("当前环境不支持创建目录符号链接")

    with pytest.raises(ValueError, match="技能路径"):
        load_skill_content(str(tmp_path), ".agents/skills/linked/SKILL.md")


def test_load_skill_content_limits_content_size(tmp_path: Path) -> None:
    write_text(
        tmp_path / ".agents" / "skills" / "large" / "SKILL.md",
        "x" * (MAX_SKILL_CONTENT_CHARS + 1),
    )

    with pytest.raises(ValueError, match="读取限制"):
        load_skill_content(str(tmp_path), ".agents/skills/large/SKILL.md")
