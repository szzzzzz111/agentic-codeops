import tomllib
from pathlib import Path

import pytest

from app.patching.parser import is_patch_proposal_request
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
        (["patch", "change app.py"], "create patch: change app.py"),
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


def test_cli_patch_request_message_triggers_existing_patch_intent() -> None:
    service = RecordingChatService()

    exit_code = _run_cli(["patch", "change README wording"], service)

    assert exit_code == 0
    message = service.requests[0].message
    assert message == "create patch: change README wording"
    assert is_patch_proposal_request(message)


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
    assert "Trace" in output
    assert "trace_123" in output
    assert "Answer" in output
    assert "grounded answer" in output
    assert "Related files" in output
    assert "- app/example.py" in output
    assert "Tool calls" in output
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


@pytest.mark.parametrize(
    "patch_id",
    [
        "patch_a",
        f"patch_{'a' * 122}",
    ],
)
def test_cli_accepts_runtime_compatible_patch_id_boundaries(patch_id: str) -> None:
    service = RecordingChatService()

    exit_code = _run_cli(["patch", "confirm", patch_id], service)

    assert exit_code == 0
    assert service.requests[0].message == f"confirm patch {patch_id}"


@pytest.mark.parametrize(
    "patch_id",
    [
        "patch_",
        f"patch_{'a' * 123}",
        "patch_abc-123",
        "id_123",
    ],
)
def test_cli_rejects_runtime_incompatible_patch_id_before_chat_service(
    patch_id: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    service = RecordingChatService()

    exit_code = _run_cli(["patch", "confirm", patch_id], service)

    captured = capsys.readouterr()
    assert exit_code == 2
    assert service.requests == []
    assert "unsupported patch id" in captured.err


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


def test_workflow_skills_define_plan_review_gates() -> None:
    stage_planner = Path(".codex/skills/openspec-stage-planner/SKILL.md").read_text(encoding="utf-8")
    workflow = Path(".codex/skills/repo-stage-workflow/SKILL.md").read_text(encoding="utf-8")
    review_loop = Path(".codex/skills/repo-stage-review-loop/SKILL.md").read_text(encoding="utf-8")

    assert "internal plan review" in stage_planner
    assert "two independent plan-review slots" in stage_planner
    assert 'fork_turns="none"' in stage_planner
    assert "inherited or unknown context" in stage_planner
    assert "same final content-addressed baseline" in stage_planner
    assert "validate_independent_review.py" in stage_planner
    assert "low-risk stage uses its explicit checklist-required slot count" in stage_planner
    assert "plan-level review" in workflow
    assert "final implementation review" in workflow
    assert "development workflow" in workflow
    assert "RepoPilot runtime" in workflow
    assert "same-slot remediation re-review" in workflow
    assert "validate_independent_review.py" in workflow
    assert "plan contract" in review_loop
    assert "same final content-addressed baseline" in review_loop
    assert "validate_independent_review.py" in review_loop


def test_opencode_plan_review_skill_limits_session_reuse() -> None:
    skill = Path(".opencode/skills/openspec-plan-review/SKILL.md").read_text(encoding="utf-8")

    assert "new isolated review session" in skill
    assert "first-round review" in skill
    assert "opencode session list" in skill
    assert "opencode run --session <session_id>" in skill
    assert "same slot's remediation re-review" in skill
    assert "MUST NOT reuse an implementation session" in skill
    assert "terminal output times out" in skill
    assert "final assistant review text" in skill
    assert "Codex review, or OpenCode review gates" not in skill
    assert "risk-contract required independent review slots" in skill
