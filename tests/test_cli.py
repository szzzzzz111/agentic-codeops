import tomllib
from pathlib import Path

import pytest

from app.schemas.chat import ChatResponse


class RecordingChatService:
    def __init__(
        self,
        response: ChatResponse | None = None,
        error: Exception | None = None,
    ) -> None:
        self.requests = []
        self._response = response or ChatResponse(
            trace_id="trace_cli",
            answer="answer text",
            related_files=["app/example.py"],
            tool_calls=[
                {
                    "tool_name": "repo_rag",
                    "status": "success",
                    "result_count": "1",
                }
            ],
        )
        self._error = error

    def handle_chat(self, request):
        self.requests.append(request)
        if self._error is not None:
            raise self._error
        return self._response


def _run_cli(args: list[str], service: RecordingChatService) -> int:
    from app import cli

    return cli.main(args, service_factory=lambda: service)


@pytest.mark.parametrize(
    ("args", "expected_message"),
    [
        (["ask", "Where is AgentLoop?"], "Where is AgentLoop?"),
        (["patch", "change app.py"], "change app.py"),
        (["patch", "confirm", "patch_20260625_abcd1234"], "confirm patch patch_20260625_abcd1234"),
        (
            ["patch", "confirm", "patch_20260625_abcd1234", "--verify", "verify"],
            "confirm patch patch_20260625_abcd1234 and run verify",
        ),
        (["verify", "pytest"], "run pytest"),
        (["verify", "ruff"], "run ruff"),
        (["verify", "verify"], "run verify"),
        (["status"], "assistant status"),
        (["audit", "latest"], "audit latest"),
    ],
)
def test_cli_maps_supported_commands_to_existing_chat_messages(
    args: list[str],
    expected_message: str,
) -> None:
    service = RecordingChatService()

    exit_code = _run_cli(args, service)

    assert exit_code == 0
    assert len(service.requests) == 1
    assert service.requests[0].message == expected_message
    assert service.requests[0].repo_path == "."
    assert service.requests[0].user_id == "cli"
    assert service.requests[0].session_id == "cli"


def test_cli_accepts_global_scope_overrides() -> None:
    service = RecordingChatService()

    exit_code = _run_cli(
        [
            "--repo",
            "mock_repo",
            "--user-id",
            "u123",
            "--session-id",
            "s456",
            "ask",
            "question",
        ],
        service,
    )

    assert exit_code == 0
    request = service.requests[0]
    assert request.repo_path == "mock_repo"
    assert request.user_id == "u123"
    assert request.session_id == "s456"


def test_cli_prints_safe_response_summary(capsys: pytest.CaptureFixture[str]) -> None:
    service = RecordingChatService(
        ChatResponse(
            trace_id="trace_123",
            answer="grounded answer",
            related_files=["app/example.py", "tests/test_example.py"],
            tool_calls=[
                {
                    "tool_name": "repo_rag",
                    "status": "success",
                    "result_count": "2",
                },
                {
                    "tool_name": "verification_run",
                    "status": "success",
                    "command_label": "verify",
                },
            ],
        )
    )

    exit_code = _run_cli(["ask", "question"], service)

    assert exit_code == 0
    output = capsys.readouterr().out
    assert "trace_id: trace_123" in output
    assert "answer:" in output
    assert "grounded answer" in output
    assert "related_files:" in output
    assert "- app/example.py" in output
    assert "tool_calls:" in output
    assert "- tool_name=repo_rag status=success result_count=2" in output
    assert "- tool_name=verification_run status=success command_label=verify" in output


@pytest.mark.parametrize(
    "args",
    [
        ["verify", "pytest -k slow"],
        ["verify", "pytest|ruff"],
        ["verify", "ruff", "--fix"],
        ["verify", "FOO=bar"],
        ["patch", "confirm", "patch_20260625_abcd1234", "--verify", "pytest -q"],
        ["patch", "confirm", "patch_20260625_abcd1234", "--verify", "verify>out.txt"],
        ["patch", "confirm", "patch_20260625_abcd1234", "--verify", "token=$(secret)"],
    ],
)
def test_cli_rejects_unsafe_verification_input_before_chat_service(
    args: list[str],
    capsys: pytest.CaptureFixture[str],
) -> None:
    service = RecordingChatService()

    exit_code = _run_cli(args, service)

    captured = capsys.readouterr()
    assert exit_code == 2
    assert service.requests == []
    assert "unsupported verification label" in captured.err
    assert "Traceback" not in captured.err


@pytest.mark.parametrize(
    "args",
    [
        ["ask", ""],
        ["patch", ""],
        ["--repo", "", "ask", "question"],
        ["--user-id", "", "ask", "question"],
        ["--session-id", "", "ask", "question"],
    ],
)
def test_cli_rejects_empty_required_values_before_chat_service(
    args: list[str],
    capsys: pytest.CaptureFixture[str],
) -> None:
    service = RecordingChatService()

    exit_code = _run_cli(args, service)

    captured = capsys.readouterr()
    assert exit_code == 2
    assert service.requests == []
    assert "must not be empty" in captured.err
    assert "Traceback" not in captured.err


@pytest.mark.parametrize(
    "patch_id",
    [
        "../patch_1",
        "patch 123",
        "patch_123;rm",
        "patch_123|verify",
        "patch_123>out",
        "patch_123$(secret)",
    ],
)
def test_cli_rejects_unsafe_patch_id_before_chat_service(
    patch_id: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    service = RecordingChatService()

    exit_code = _run_cli(["patch", "confirm", patch_id], service)

    captured = capsys.readouterr()
    assert exit_code == 2
    assert service.requests == []
    assert "unsupported patch id" in captured.err
    assert "Traceback" not in captured.err


def test_cli_returns_usage_exit_code_without_raw_traceback(
    capsys: pytest.CaptureFixture[str],
) -> None:
    service = RecordingChatService()

    exit_code = _run_cli(["audit", "everything"], service)

    captured = capsys.readouterr()
    assert exit_code == 2
    assert service.requests == []
    assert "Traceback" not in captured.err


def test_cli_returns_wrapper_failure_without_raw_traceback(
    capsys: pytest.CaptureFixture[str],
) -> None:
    service = RecordingChatService(error=RuntimeError("secret stack detail"))

    exit_code = _run_cli(["ask", "question"], service)

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "CLI error" in captured.err
    assert "secret stack detail" not in captured.err
    assert "Traceback" not in captured.err


def test_pyproject_exposes_repopilot_console_script() -> None:
    pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

    assert pyproject["project"]["scripts"]["repopilot"] == "app.cli:main"
