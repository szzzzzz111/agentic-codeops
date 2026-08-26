import subprocess
import sys
from pathlib import Path

import pytest

import app.verification.runner as verification_runner
from app.verification.runner import (
    MAX_ANSWER_OUTPUT_CHARS,
    MAX_STREAM_EXCERPT_CHARS,
    VerificationRunResult,
    command_argv,
    format_verification_answer,
    parse_verification_label,
    parse_verification_request,
    redact_verification_output,
    run_verification_command,
    run_whitelisted_verification,
)


def test_parser_accepts_only_fixed_verification_labels() -> None:
    assert parse_verification_request("运行验证").command_label == "verify"
    assert parse_verification_request("run verify").command_label == "verify"
    assert parse_verification_request("运行 pytest").command_label == "pytest"
    assert parse_verification_request("run ruff").command_label == "ruff"


def test_parser_rejects_arguments_shell_syntax_and_mutating_commands() -> None:
    rejected_messages = [
        "运行 pytest tests/test_chat_api.py",
        "run pytest -k chat",
        "run ruff --fix",
        "run verify | more",
        "run verify > out.txt",
        "TOKEN=secret run pytest",
    ]

    for message in rejected_messages:
        parsed = parse_verification_request(message)
        assert parsed.handled is True
        assert parsed.rejected is True


def test_patch_verify_label_parser_uses_same_whitelist_boundaries() -> None:
    assert parse_verification_label("验证").command_label == "verify"
    assert parse_verification_label("verify").command_label == "verify"
    assert parse_verification_label("pytest").command_label == "pytest"
    assert parse_verification_label("ruff").command_label == "ruff"

    for value in ("", "pytest tests/test_chat_api.py", "ruff --fix", "verify | more"):
        parsed = parse_verification_label(value)
        assert parsed.handled is True
        assert parsed.rejected is True


def test_runner_summarizes_nonzero_exit_and_redacts_output(tmp_path: Path) -> None:
    script = tmp_path / "fail.py"
    script.write_text(
        "import sys\n"
        "print(r'C:\\\\Users\\\\me\\\\repo\\\\file.py API_KEY=super-secret')\n"
        "print('.repopilot/patches.sqlite3 TOKEN=abc123', file=sys.stderr)\n"
        "sys.exit(3)\n",
        encoding="utf-8",
    )

    result = run_verification_command(
        repo_path=tmp_path,
        command_label="custom",
        argv=[sys.executable, str(script)],
        timeout_seconds=10,
    )

    assert result.status == "failed"
    assert result.exit_code == 3
    assert result.timed_out is False
    assert "C:\\Users" not in result.stdout_excerpt
    assert "<local-path>" in result.stdout_excerpt
    assert "super-secret" not in result.stdout_excerpt
    assert ".repopilot/<redacted>" in result.stderr_excerpt
    assert "abc123" not in result.stderr_excerpt
    assert result.truncated is False


def test_runner_handles_missing_command_without_leaking_repo_path(tmp_path: Path) -> None:
    result = run_verification_command(
        repo_path=tmp_path,
        command_label="missing",
        argv=["definitely-missing-repopilot-command"],
        timeout_seconds=10,
    )

    assert result.status == "unavailable"
    assert result.exit_code is None
    assert str(tmp_path) not in result.stderr_excerpt


def test_runner_times_out_and_truncates_output(tmp_path: Path) -> None:
    script = tmp_path / "slow.py"
    script.write_text(
        "import time\n"
        "print('x' * 5000, flush=True)\n"
        "time.sleep(5)\n",
        encoding="utf-8",
    )

    result = run_verification_command(
        repo_path=tmp_path,
        command_label="slow",
        argv=[sys.executable, str(script)],
        timeout_seconds=1,
    )

    assert result.status == "timed_out"
    assert result.timed_out is True
    assert result.truncated is True
    assert len(result.stdout_excerpt) <= MAX_STREAM_EXCERPT_CHARS


def test_redaction_replaces_repo_path_local_paths_repopilot_and_secrets(
    tmp_path: Path,
) -> None:
    raw = (
        f"{tmp_path}\\app.py\n"
        "C:\\Users\\me\\repo\\secret.py\n"
        "/home/me/repo/secret.py\n"
        ".repopilot/tasks.sqlite3\n"
        "PASSWORD=hunter2 SECRET='abc' TOKEN=xyz API_KEY=\"key\" OPENAI_API_KEY=real\n"
    )

    redacted = redact_verification_output(raw, repo_path=tmp_path)

    assert str(tmp_path) not in redacted
    assert "<repo>" in redacted
    assert "<local-path>" in redacted
    assert ".repopilot/<redacted>" in redacted
    assert "hunter2" not in redacted
    assert "abc" not in redacted
    assert "xyz" not in redacted
    assert "key" not in redacted
    assert "real" not in redacted


def test_answer_marks_truncated_when_combined_output_exceeds_answer_limit() -> None:
    result = VerificationRunResult(
        command_label="verify",
        status="failed",
        exit_code=1,
        duration_ms=5,
        stdout_excerpt="a" * 3500,
        stderr_excerpt="b" * 3500,
        truncated=False,
    )

    answer = format_verification_answer(result)

    assert "truncated=true" in answer
    assert len(answer) <= MAX_ANSWER_OUTPUT_CHARS + 120


def test_whitelisted_argv_uses_isolated_current_interpreter() -> None:
    assert command_argv("pytest") == [sys.executable, "-I", "-m", "pytest"]
    assert command_argv("ruff") == [
        sys.executable,
        "-I",
        "-m",
        "ruff",
        "check",
        ".",
    ]
    assert command_argv("verify") == [
        sys.executable,
        "-I",
        "scripts/verify.py",
    ]


def test_missing_pytest_module_fails_before_tool_spawn(
    monkeypatch,
    tmp_path: Path,
) -> None:
    calls: list[list[str]] = []

    def fake_run(argv, **kwargs):
        calls.append(list(argv))
        return subprocess.CompletedProcess(argv, 1, "", "missing")

    monkeypatch.setattr(verification_runner.subprocess, "run", fake_run)

    result = run_whitelisted_verification(tmp_path, "pytest")

    assert result.status == "unavailable"
    assert result.stderr_excerpt == "verification_tool_unavailable:pytest"
    assert len(calls) == 1
    assert calls[0][1:3] == ["-I", "-c"]


def test_pytest_probe_exception_fails_before_tool_spawn(
    monkeypatch,
    tmp_path: Path,
) -> None:
    calls: list[list[str]] = []

    def fake_run(argv, **kwargs):
        calls.append(list(argv))
        raise subprocess.TimeoutExpired(argv, 1)

    monkeypatch.setattr(verification_runner.subprocess, "run", fake_run)

    result = run_whitelisted_verification(tmp_path, "pytest", timeout_seconds=1)

    assert result.status == "unavailable"
    assert result.stderr_excerpt == "verification_tool_unavailable:pytest"
    assert len(calls) == 1


def test_whitelisted_runner_rejects_missing_repo_before_probe(tmp_path: Path) -> None:
    result = run_whitelisted_verification(tmp_path / "missing", "pytest")

    assert result.status == "unavailable"
    assert result.stderr_excerpt == "repo_unavailable"


def test_pytest_spawn_uses_controlled_environment(
    monkeypatch,
    tmp_path: Path,
) -> None:
    calls: list[tuple[list[str], dict[str, str]]] = []

    def fake_run(argv, **kwargs):
        calls.append((list(argv), dict(kwargs.get("env", {}))))
        return subprocess.CompletedProcess(argv, 0, "ok", "")

    monkeypatch.setenv("PYTEST_ADDOPTS", "--collect-only")
    monkeypatch.setenv("PYTEST_PLUGINS", "hostile_plugin")
    monkeypatch.setattr(verification_runner.subprocess, "run", fake_run)

    result = run_whitelisted_verification(tmp_path, "pytest")

    assert result.status == "success"
    assert len(calls) == 2
    for _, env in calls:
        assert "PYTEST_ADDOPTS" not in env
        assert "PYTEST_PLUGINS" not in env
        assert env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] == "1"


def test_pytest_ignores_collect_only_and_executes_test_body(
    monkeypatch,
    tmp_path: Path,
) -> None:
    marker = tmp_path / "executed.txt"
    (tmp_path / "test_marker.py").write_text(
        "from pathlib import Path\n\n"
        "def test_body_runs():\n"
        f"    Path({str(marker)!r}).write_text('yes', encoding='utf-8')\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("PYTEST_ADDOPTS", "--collect-only")
    monkeypatch.setenv("PYTEST_PLUGINS", "hostile_plugin")

    result = run_whitelisted_verification(tmp_path, "pytest", timeout_seconds=20)

    assert result.status == "success"
    assert marker.read_text(encoding="utf-8") == "yes"


@pytest.mark.parametrize("label", ["pytest", "ruff"])
@pytest.mark.parametrize("shadow_kind", ["module", "package"])
def test_isolated_verification_ignores_repo_and_pythonpath_shadow_tools(
    monkeypatch,
    tmp_path: Path,
    label: str,
    shadow_kind: str,
) -> None:
    marker = tmp_path / f"{label}-{shadow_kind}-loaded.txt"
    shadow_source = (
        "from pathlib import Path\n"
        f"Path({str(marker)!r}).write_text('loaded', encoding='utf-8')\n"
    )
    if shadow_kind == "module":
        (tmp_path / f"{label}.py").write_text(shadow_source, encoding="utf-8")
    else:
        package = tmp_path / label
        package.mkdir()
        (package / "__init__.py").write_text(shadow_source, encoding="utf-8")
    monkeypatch.setenv("PYTHONPATH", str(tmp_path))

    result = run_whitelisted_verification(tmp_path, label, timeout_seconds=20)

    assert result.status == "failed"
    assert not marker.exists()


def test_installed_ruff_is_available_from_fixture_repository(tmp_path: Path) -> None:
    result = run_whitelisted_verification(tmp_path, "ruff", timeout_seconds=20)

    assert result.status == "success"


def test_redaction_removes_current_interpreter_paths(tmp_path: Path) -> None:
    raw = f"failed under {sys.executable} and {Path(sys.executable).resolve()}"

    redacted = redact_verification_output(raw, repo_path=tmp_path)

    assert sys.executable not in redacted
    assert str(Path(sys.executable).resolve()) not in redacted


def test_interpreter_path_is_redacted_from_result_answer_and_audit(
    tmp_path: Path,
) -> None:
    result = run_verification_command(
        repo_path=tmp_path,
        command_label="custom",
        argv=[sys.executable, "-c", "import sys; print(sys.executable)"],
        timeout_seconds=10,
    )

    assert result.status == "success"
    assert "<python>" in result.stdout_excerpt
    assert sys.executable not in result.stdout_excerpt
    assert sys.executable not in format_verification_answer(result)
    assert sys.executable not in str(result.audit_summary())
