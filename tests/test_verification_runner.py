from pathlib import Path

from app.verification.runner import (
    MAX_ANSWER_OUTPUT_CHARS,
    MAX_STREAM_EXCERPT_CHARS,
    VerificationRunResult,
    format_verification_answer,
    parse_verification_request,
    parse_verification_label,
    redact_verification_output,
    run_verification_command,
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
        argv=["python", str(script)],
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
        argv=["python", str(script)],
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
