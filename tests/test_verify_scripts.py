from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from scripts import check_skill_evals, check_stage_docs
from scripts import verify as verify_script

REPO_ROOT = Path(__file__).resolve().parent.parent


def _write(path: Path, content: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _valid_stage_docs_fixture(root: Path) -> None:
    for relative in check_stage_docs.REQUIRED_FILES:
        _write(root / relative)
    _write(root / "README.md", "# RepoPilot\n")
    _write(
        root / "HANDOFF_TO_NEXT_CHAT.md",
        "Active OpenSpec change: example\n"
        "git status --short --branch\n"
        "git log -5 --oneline --decorate\n"
        "openspec list\n",
    )
    _write(
        root / "openspec/specs/harness-development-workflow/spec.md",
        "# workflow\n"
        "Progress And Handoff Have Separate Ownership\n"
        "Stage Debt Sweep Is Focused And Checkable\n"
        "Stage Workflow Is Risk-Scaled\n"
        "External Review Seeks Independent Counterexamples\n"
        "Archive Freezes Reviewed Runtime\n",
    )
    _write(root / "docs/PROGRESS.md", "# Progress\n\n## 下一步建议\n\nContinue.\n")


def _valid_skill_eval_fixture(root: Path) -> None:
    for relative in check_skill_evals.SKILLS:
        _write(
            root / relative / "SKILL.md",
            "description: Use when repository stage work is requested\n\n"
            "See references/evals.md.\n",
        )
        _write(
            root / relative / "references/evals.md",
            "\n\n".join(check_skill_evals.REQUIRED_SECTIONS) + "\n",
        )


def test_verify_entry_isolated_from_caller_cwd_and_pythonpath(tmp_path: Path) -> None:
    sitecustomize = tmp_path / "sitecustomize.py"
    sitecustomize.write_text("raise SystemExit(0)\n", encoding="utf-8")
    env = {"PYTHONPATH": str(tmp_path), "PYTEST_ADDOPTS": "--collect-only"}

    result = subprocess.run(
        [sys.executable, "-I", str(REPO_ROOT / "scripts" / "verify.py"), "--help"],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "canonical repository verification" in result.stdout.lower()


def test_python_scanners_pass_for_repository() -> None:
    for script_name in ("check_stage_docs.py", "check_skill_evals.py"):
        result = subprocess.run(
            [sys.executable, "-I", str(REPO_ROOT / "scripts" / script_name)],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stdout + result.stderr


def test_powershell_wrappers_are_thin_isolated_delegates() -> None:
    expected_driver = {
        "verify.ps1": "verify.py",
        "check_stage_docs.ps1": "check_stage_docs.py",
        "check_skill_evals.ps1": "check_skill_evals.py",
    }
    for wrapper, driver in expected_driver.items():
        text = (REPO_ROOT / "scripts" / wrapper).read_text(encoding="utf-8")
        assert driver in text
        assert "-I" in text
        assert "pytest" not in text
        assert "ruff check" not in text
        assert "[Console]::Error.WriteLine" in text
        assert "exit 2" in text


def test_verify_probe_exception_fails_closed(monkeypatch, tmp_path: Path) -> None:
    def fail_probe(*args, **kwargs):
        raise subprocess.TimeoutExpired(args[0], 1)

    monkeypatch.setattr(verify_script.subprocess, "run", fail_probe)

    assert verify_script._module_available("pytest", cwd=tmp_path, env={}) is False


def test_verify_sequence_uses_fixed_root_environment_and_stops_on_failure(
    monkeypatch,
) -> None:
    calls: list[tuple[list[str], Path, dict[str, str]]] = []

    def fake_run(argv, **kwargs):
        calls.append((list(argv), Path(kwargs["cwd"]), dict(kwargs["env"])))
        if argv[1:5] == ["-I", "-m", "ruff", "check"]:
            return subprocess.CompletedProcess(argv, 7)
        return subprocess.CompletedProcess(argv, 0)

    monkeypatch.setenv("PYTEST_ADDOPTS", "--collect-only")
    monkeypatch.setenv("PYTEST_PLUGINS", "hostile_plugin")
    monkeypatch.setattr(verify_script.subprocess, "run", fake_run)
    monkeypatch.setattr(sys, "argv", ["verify.py"])

    assert verify_script.main() == 7
    assert len(calls) == 4
    assert calls[2][0] == [sys.executable, "-I", "-m", "pytest"]
    assert calls[3][0] == [sys.executable, "-I", "-m", "ruff", "check", "."]
    for _, cwd, env in calls:
        assert cwd == REPO_ROOT
        assert "PYTEST_ADDOPTS" not in env
        assert "PYTEST_PLUGINS" not in env
        assert env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] == "1"


def test_verify_success_sequence_runs_all_required_commands(monkeypatch) -> None:
    calls: list[tuple[list[str], Path, dict[str, str]]] = []

    def fake_run(argv, **kwargs):
        calls.append((list(argv), Path(kwargs["cwd"]), dict(kwargs["env"])))
        return subprocess.CompletedProcess(argv, 0)

    monkeypatch.setattr(verify_script.subprocess, "run", fake_run)
    monkeypatch.setattr(sys, "argv", ["verify.py"])
    caller = REPO_ROOT.parent
    monkeypatch.chdir(caller)

    assert verify_script.main() == 0
    assert [call[0] for call in calls[2:]] == [
        [sys.executable, "-I", "-m", "pytest"],
        [sys.executable, "-I", "-m", "ruff", "check", "."],
        [sys.executable, "-I", "scripts/check_stage_docs.py"],
        [sys.executable, "-I", "scripts/check_skill_evals.py"],
    ]
    assert all(cwd == REPO_ROOT for _, cwd, _ in calls)


def test_canonical_verify_real_fixture_blocks_ambient_shadow_and_collect_only(
    tmp_path: Path,
) -> None:
    fixture = tmp_path / "fixture-repo"
    scripts = fixture / "scripts"
    scripts.mkdir(parents=True)
    shutil.copy2(REPO_ROOT / "scripts/verify.py", scripts / "verify.py")
    pytest_marker = fixture / "pytest-ran.txt"
    stage_marker = fixture / "stage-scan-ran.txt"
    skill_marker = fixture / "skill-scan-ran.txt"
    _write(
        fixture / "test_marker.py",
        "# ruff: noqa\n"
        "from pathlib import Path\n\n"
        "def test_body_runs():\n"
        f"    Path({str(pytest_marker)!r}).write_text('yes', encoding='utf-8')\n",
    )
    for script_name, marker in (
        ("check_stage_docs.py", stage_marker),
        ("check_skill_evals.py", skill_marker),
    ):
        _write(
            scripts / script_name,
            "# ruff: noqa\n"
            "from pathlib import Path\n"
            f"Path({str(marker)!r}).write_text('yes', encoding='utf-8')\n",
        )
    hostile = tmp_path / "hostile-pythonpath"
    hostile.mkdir()
    shadow_marker = tmp_path / "shadow-loaded.txt"
    shadow_source = (
        "from pathlib import Path\n"
        f"Path({str(shadow_marker)!r}).write_text('loaded', encoding='utf-8')\n"
    )
    _write(hostile / "pytest.py", shadow_source)
    _write(hostile / "ruff.py", shadow_source)
    caller = tmp_path / "caller"
    caller.mkdir()
    env = os.environ.copy()
    env["PYTHONPATH"] = str(hostile)
    env["PYTEST_ADDOPTS"] = "--collect-only"
    env["PYTEST_PLUGINS"] = "hostile_plugin"

    result = subprocess.run(
        [sys.executable, "-I", str(scripts / "verify.py")],
        cwd=caller,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert pytest_marker.read_text(encoding="utf-8") == "yes"
    assert stage_marker.read_text(encoding="utf-8") == "yes"
    assert skill_marker.read_text(encoding="utf-8") == "yes"
    assert not shadow_marker.exists()


@pytest.mark.parametrize(
    "case",
    [
        "required_file",
        "purpose_placeholder",
        "handoff_marker",
        "handoff_version",
        "handoff_current_head",
        "workflow_requirement",
        "current_fact_stale",
        "progress_heading",
        "progress_stale",
        "progress_v24",
        "readme_heading",
    ],
)
def test_stage_doc_scanner_covers_each_failure_family(
    tmp_path: Path,
    case: str,
) -> None:
    _valid_stage_docs_fixture(tmp_path)
    assert check_stage_docs.scan(tmp_path) == []

    if case == "required_file":
        (tmp_path / "AGENTS.md").unlink()
    elif case == "purpose_placeholder":
        _write(tmp_path / "openspec/specs/example/spec.md", "Purpose: TODO\n")
    elif case == "handoff_marker":
        handoff = tmp_path / "HANDOFF_TO_NEXT_CHAT.md"
        handoff.write_text(
            handoff.read_text(encoding="utf-8").replace("openspec list\n", ""),
            encoding="utf-8",
        )
    elif case == "handoff_version":
        handoff = tmp_path / "HANDOFF_TO_NEXT_CHAT.md"
        handoff.write_text(
            handoff.read_text(encoding="utf-8") + "\n## V1\n",
            encoding="utf-8",
        )
    elif case == "handoff_current_head":
        handoff = tmp_path / "HANDOFF_TO_NEXT_CHAT.md"
        handoff.write_text(
            handoff.read_text(encoding="utf-8") + "current HEAD is abcdef1\n",
            encoding="utf-8",
        )
    elif case == "workflow_requirement":
        workflow = tmp_path / "openspec/specs/harness-development-workflow/spec.md"
        workflow.write_text(
            workflow.read_text(encoding="utf-8").replace(
                "Archive Freezes Reviewed Runtime", ""
            ),
            encoding="utf-8",
        )
    elif case == "current_fact_stale":
        _write(tmp_path / "README.md", "# RepoPilot\narchive pending\n")
    elif case == "progress_heading":
        _write(tmp_path / "docs/PROGRESS.md", "# Progress\n")
    elif case == "progress_stale":
        _write(
            tmp_path / "docs/PROGRESS.md",
            "# Progress\n\n## 下一步建议\n\nmerge pending\n",
        )
    elif case == "progress_v24":
        _write(
            tmp_path / "docs/PROGRESS.md",
            "# Progress\n\n## 下一步建议\n\nV24 CLI surface\n",
        )
    else:
        _write(tmp_path / "README.md", "# RepoPilot\n\n## 当前能力\n")

    assert check_stage_docs.scan(tmp_path)


def test_stage_doc_scanner_preserves_case_insensitive_placeholder_checks(
    tmp_path: Path,
) -> None:
    _valid_stage_docs_fixture(tmp_path)
    _write(tmp_path / "openspec/specs/example/spec.md", "Purpose: tOdO\n")

    assert check_stage_docs.scan(tmp_path)


@pytest.mark.parametrize(
    "case",
    [
        "skill_missing",
        "eval_missing",
        "description_missing",
        "description_prefix",
        "description_length",
        "eval_reference",
        "positive",
        "negative",
        "edge",
        "failure_traps",
    ],
)
def test_skill_eval_scanner_covers_each_failure_family(
    tmp_path: Path,
    case: str,
) -> None:
    _valid_skill_eval_fixture(tmp_path)
    assert check_skill_evals.scan(tmp_path) == []
    skill_root = tmp_path / check_skill_evals.SKILLS[0]

    if case == "skill_missing":
        (skill_root / "SKILL.md").unlink()
    elif case == "eval_missing":
        (skill_root / "references/evals.md").unlink()
    elif case == "description_missing":
        _write(skill_root / "SKILL.md", "See references/evals.md.\n")
    elif case == "description_prefix":
        _write(
            skill_root / "SKILL.md",
            "description: Run when repository stage work is requested\n"
            "See references/evals.md.\n",
        )
    elif case == "description_length":
        _write(
            skill_root / "SKILL.md",
            "description: Use when " + ("word " * 51) + "\nreferences/evals.md\n",
        )
    elif case == "eval_reference":
        _write(
            skill_root / "SKILL.md",
            "description: Use when repository stage work is requested\n",
        )
    else:
        heading = {
            "positive": "## Positive",
            "negative": "## Negative",
            "edge": "## Edge",
            "failure_traps": "## Failure Traps",
        }[case]
        eval_path = skill_root / "references/evals.md"
        eval_path.write_text(
            eval_path.read_text(encoding="utf-8").replace(heading, ""),
            encoding="utf-8",
        )

    assert check_skill_evals.scan(tmp_path)


def test_skill_eval_scanner_preserves_case_insensitive_match_semantics(
    tmp_path: Path,
) -> None:
    _valid_skill_eval_fixture(tmp_path)
    for relative in check_skill_evals.SKILLS:
        _write(
            tmp_path / relative / "SKILL.md",
            "description: use when repository stage work is requested\n\n"
            "See REFERENCES/EVALS.MD.\n",
        )
        _write(
            tmp_path / relative / "references/evals.md",
            "## positive\n\n## negative\n\n## edge\n\n## failure traps\n",
        )

    assert check_skill_evals.scan(tmp_path) == []
