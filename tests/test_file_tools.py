from pathlib import Path

import pytest

from app.tools.file_tools import list_files, read_file, search_code


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_bytes(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def test_list_files_returns_normal_code_files(tmp_path: Path) -> None:
    write_text(tmp_path / "app.py", "def hello():\n    return 'hi'\n")
    write_text(tmp_path / "pkg" / "service.py", "class Service:\n    pass\n")

    assert list_files(str(tmp_path)) == ["app.py", "pkg/service.py"]


def test_list_files_skips_sensitive_files_and_hidden_directories(
    tmp_path: Path,
) -> None:
    write_text(tmp_path / "app.py", "print('ok')\n")
    write_text(tmp_path / ".env", "API_KEY=secret\n")
    write_text(tmp_path / ".netrc", "machine example.com login user password secret\n")
    write_text(tmp_path / ".npmrc", "//registry.npmjs.org/:_authToken=secret\n")
    write_text(tmp_path / ".pypirc", "[pypi]\npassword=secret\n")
    write_text(tmp_path / "private.key", "secret\n")
    write_text(tmp_path / ".git" / "config", "hidden\n")
    write_text(tmp_path / ".hidden" / "notes.py", "hidden\n")
    write_text(tmp_path / "__pycache__" / "cache.pyc", "cache\n")
    write_text(tmp_path / ".venv" / "lib.py", "venv\n")
    write_text(tmp_path / "node_modules" / "pkg.js", "module\n")
    write_bytes(tmp_path / "image.png", b"\x89PNG\x00binary")

    assert list_files(str(tmp_path)) == ["app.py"]


def test_read_file_reads_repo_file(tmp_path: Path) -> None:
    write_text(tmp_path / "calculator.py", "def add(a, b):\n    return a + b\n")

    assert read_file(str(tmp_path), "calculator.py") == (
        "def add(a, b):\n    return a + b\n"
    )


def test_read_file_limits_max_chars(tmp_path: Path) -> None:
    write_text(tmp_path / "long.py", "abcdef")

    assert read_file(str(tmp_path), "long.py", max_chars=3) == "abc"


def test_read_file_rejects_repo_escape(tmp_path: Path) -> None:
    outside_file = tmp_path.parent / "outside.py"
    write_text(outside_file, "print('outside')\n")

    with pytest.raises(ValueError, match="路径逃逸仓库"):
        read_file(str(tmp_path), "../outside.py")


def test_read_file_rejects_sensitive_file(tmp_path: Path) -> None:
    write_text(tmp_path / ".env", "TOKEN=secret\n")

    with pytest.raises(ValueError, match="不允许访问"):
        read_file(str(tmp_path), ".env")


def test_search_code_returns_matching_file_line_and_text(tmp_path: Path) -> None:
    write_text(
        tmp_path / "calculator.py",
        "def add(a, b):\n    return a + b\n",
    )

    assert search_code(str(tmp_path), "return") == [
        {
            "file_path": "calculator.py",
            "line_number": 2,
            "line_text": "return a + b",
        }
    ]


def test_search_code_returns_empty_list_when_keyword_is_missing(
    tmp_path: Path,
) -> None:
    write_text(tmp_path / "calculator.py", "def add(a, b):\n    return a + b\n")

    assert search_code(str(tmp_path), "divide") == []


def test_search_code_does_not_return_sensitive_file_content(tmp_path: Path) -> None:
    write_text(tmp_path / "app.py", "TOKEN = 'placeholder'\n")
    write_text(tmp_path / ".env", "TOKEN=real-secret\n")

    results = search_code(str(tmp_path), "TOKEN")

    assert results == [
        {
            "file_path": "app.py",
            "line_number": 1,
            "line_text": "TOKEN = 'placeholder'",
        }
    ]


def test_search_code_limits_max_results(tmp_path: Path) -> None:
    write_text(tmp_path / "a.py", "needle\nneedle\n")
    write_text(tmp_path / "b.py", "needle\n")

    assert len(search_code(str(tmp_path), "needle", max_results=2)) == 2
