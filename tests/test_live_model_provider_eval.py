from __future__ import annotations

from dataclasses import asdict
from decimal import Decimal
import json
from pathlib import Path
import subprocess

import httpx
import pytest

from app.agents.code_agent import CodeAgent
from app.harness.kernel import AgentLoop
from app.services.chat_service import ChatService
from app.providers.model_provider import OpenAICompatibleModelProvider
from app.providers.model_provider import ProviderCallMetrics
from app.providers.model_provider import ModelProviderResponse
from evals.live_model_provider.api_smoke import extract_default_agent_loop
from evals.live_model_provider.cases import (
    RecordingModelProvider,
    load_eval_cases,
    run_grounded_case,
    run_no_answer_case,
    run_secret_filter_check,
)
from evals.live_model_provider.components import (
    run_api_subprocess_case,
    run_patch_case,
    run_planner_case,
)
from evals.live_model_provider.runner import (
    GitState,
    run_live_evaluation,
)
from evals.live_model_provider.core import (
    DEEPSEEK_V4_FLASH_PROFILE,
    CallBudget,
    CaseResult,
    LiveEvalReport,
    build_attestation,
    calculate_cost_cny,
    evaluate_required_facts,
    validate_live_environment,
    validate_provider_metrics,
    write_local_report,
)


REQUIRED_ENV = {
    "REPOPILOT_MODEL_PROVIDER": "openai_compatible",
    "REPOPILOT_MODEL_BASE_URL": "https://api.deepseek.com",
    "REPOPILOT_MODEL_API_KEY": "TEST_API_KEY_CANARY",
    "REPOPILOT_MODEL_NAME": "deepseek-v4-flash",
    "REPOPILOT_MODEL_THINKING": "disabled",
}


def complete_metrics() -> ProviderCallMetrics:
    return ProviderCallMetrics(
        availability="available",
        latency_ms=125,
        requested_model="deepseek-v4-flash",
        returned_model="deepseek-v4-flash",
        system_fingerprint="fp_private",
        finish_reason="stop",
        finish_reason_status="complete",
        prompt_tokens=100,
        prompt_cache_hit_tokens=40,
        prompt_cache_miss_tokens=60,
        completion_tokens=20,
        reasoning_tokens=5,
        total_tokens=120,
    )


def test_live_environment_missing_value_skips_without_echoing_secret() -> None:
    env = dict(REQUIRED_ENV)
    env.pop("REPOPILOT_MODEL_API_KEY")

    result = validate_live_environment(env, DEEPSEEK_V4_FLASH_PROFILE)

    assert result.status == "skip"
    assert result.exit_code == 0
    assert result.reasons == ["missing:REPOPILOT_MODEL_API_KEY"]
    assert "TEST_API_KEY_CANARY" not in repr(result)


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("REPOPILOT_MODEL_PROVIDER", "fake"),
        ("REPOPILOT_MODEL_BASE_URL", "https://api.deepseek.com/v1"),
        ("REPOPILOT_MODEL_NAME", "deepseek-v4-pro"),
        ("REPOPILOT_MODEL_THINKING", "enabled"),
    ],
)
def test_complete_but_mismatched_profile_fails_before_network(
    name: str,
    value: str,
) -> None:
    env = {**REQUIRED_ENV, name: value}

    result = validate_live_environment(env, DEEPSEEK_V4_FLASH_PROFILE)

    assert result.status == "fail"
    assert result.exit_code == 1
    assert result.reasons == [f"profile_mismatch:{name}"]


def test_live_environment_ready_keeps_api_key_out_of_result() -> None:
    result = validate_live_environment(REQUIRED_ENV, DEEPSEEK_V4_FLASH_PROFILE)

    assert result.status == "ready"
    assert result.exit_code == 0
    assert "TEST_API_KEY_CANARY" not in repr(result)
    assert not hasattr(result, "api_key")


def test_call_budget_allows_eight_unique_single_calls_and_fails_closed() -> None:
    budget = CallBudget(max_calls=8)
    for index in range(8):
        budget.consume(f"case_{index}")

    assert budget.used == 8
    with pytest.raises(ValueError, match="live call budget exceeded"):
        budget.consume("case_8")
    with pytest.raises(ValueError, match="case already called"):
        budget.consume("case_0")


def test_deepseek_metrics_require_stop_and_complete_usage() -> None:
    assert validate_provider_metrics(complete_metrics()) == []

    incomplete = ProviderCallMetrics(
        **{
            **asdict(complete_metrics()),
            "finish_reason": "length",
            "finish_reason_status": "incomplete",
            "prompt_cache_miss_tokens": None,
        }
    )

    assert validate_provider_metrics(incomplete) == [
        "finish_reason_not_stop",
        "usage_incomplete",
    ]


def test_deepseek_metrics_reject_model_and_usage_relationship_mismatch() -> None:
    wrong_model = ProviderCallMetrics(
        **{
            **asdict(complete_metrics()),
            "returned_model": "deepseek-v4-pro",
        }
    )
    wrong_split = ProviderCallMetrics(
        **{
            **asdict(complete_metrics()),
            "prompt_cache_miss_tokens": 59,
        }
    )
    wrong_total = ProviderCallMetrics(
        **{
            **asdict(complete_metrics()),
            "total_tokens": 119,
        }
    )
    negative_usage = ProviderCallMetrics(
        **{
            **asdict(complete_metrics()),
            "prompt_tokens": -1,
            "prompt_cache_hit_tokens": -1,
            "prompt_cache_miss_tokens": 0,
            "total_tokens": 19,
        }
    )

    assert validate_provider_metrics(wrong_model) == ["returned_model_mismatch"]
    assert validate_provider_metrics(wrong_split) == ["prompt_token_split_mismatch"]
    assert validate_provider_metrics(wrong_total) == ["total_token_count_mismatch"]
    assert validate_provider_metrics(negative_usage) == ["usage_negative"]


def test_cost_uses_cache_split_and_does_not_double_charge_reasoning() -> None:
    cost = calculate_cost_cny(complete_metrics(), DEEPSEEK_V4_FLASH_PROFILE)

    assert cost == Decimal("0.0001008")


def test_cost_is_unavailable_when_usage_is_incomplete() -> None:
    metrics = ProviderCallMetrics(
        **{
            **asdict(complete_metrics()),
            "prompt_cache_hit_tokens": None,
        }
    )

    assert calculate_cost_cny(metrics, DEEPSEEK_V4_FLASH_PROFILE) is None


def test_required_facts_score_is_case_insensitive_and_all_or_nothing() -> None:
    assert evaluate_required_facts(
        "Use REPOPILOT_MODEL_NAME and thinking=disabled.",
        ["repopilot_model_name", "THINKING=DISABLED"],
    )
    assert not evaluate_required_facts(
        "Use REPOPILOT_MODEL_NAME.",
        ["REPOPILOT_MODEL_NAME", "thinking=disabled"],
    )


def test_report_and_attestation_use_allowlists_and_never_store_raw_content(
    tmp_path: Path,
) -> None:
    report = LiveEvalReport(
        status="pass",
        tested_commit="abc123",
        started_at="2026-06-22T12:00:00Z",
        completed_at="2026-06-22T12:01:00Z",
        profile=DEEPSEEK_V4_FLASH_PROFILE,
        rubric_version="2026-06-22",
        call_count=1,
        quality_passed=1,
        quality_total=5,
        cases=[
            CaseResult(
                case_id="configuration",
                status="pass",
                hard_gate_failures=[],
                quality_passed=True,
                metrics=complete_metrics(),
                cost_cny=Decimal("0.0001008"),
            )
        ],
    )

    report_path, digest = write_local_report(report, tmp_path / ".repopilot")
    payload_text = report_path.read_text(encoding="utf-8")
    payload = json.loads(payload_text)

    assert payload["status"] == "pass"
    assert payload["cases"][0]["metrics"]["system_fingerprint_status"] == "available"
    for forbidden in (
        "test_api_key_canary",
        "fp_private",
        "raw_prompt",
        "full_prompt",
        "raw_answer",
        "evidence_pack",
        "diff_text",
        "reasoning_content",
    ):
        assert forbidden not in payload_text.lower()

    attestation = build_attestation(report, local_report_sha256=digest)
    attestation_text = json.dumps(attestation, ensure_ascii=False)
    assert attestation["tested_commit"] == "abc123"
    assert attestation["local_report_sha256"] == digest
    assert attestation["quality_baseline"] == {"passed": 1, "total": 5}
    assert "fp_private" not in attestation_text


def test_non_pass_report_cannot_create_attestation() -> None:
    report = LiveEvalReport(
        status="fail",
        tested_commit="abc123",
        started_at="2026-06-22T12:00:00Z",
        completed_at="2026-06-22T12:01:00Z",
        profile=DEEPSEEK_V4_FLASH_PROFILE,
        rubric_version="2026-06-22",
        call_count=1,
        quality_passed=0,
        quality_total=5,
        cases=[],
    )

    with pytest.raises(ValueError, match="PASS report required"):
        build_attestation(report, local_report_sha256="0" * 64)


class StaticProvider:
    def __init__(self, answer: str) -> None:
        self.answer = answer
        self.calls = 0

    def generate(self, request) -> ModelProviderResponse:
        self.calls += 1
        return ModelProviderResponse(
            answer=self.answer,
            audit_summary={
                "provider": "static",
                "model": "static",
                "status": "success",
            },
            metrics=complete_metrics(),
        )


class FailIfCalledProvider:
    def generate(self, request) -> ModelProviderResponse:
        raise AssertionError("provider must not be called")


def test_fixed_cases_cover_required_quality_and_safety_categories() -> None:
    cases = load_eval_cases()

    assert {case.case_id for case in cases} == {
        "code_location",
        "implementation_explanation",
        "configuration",
        "test_validation",
        "ambiguous",
        "no_answer",
        "prompt_injection",
    }
    quality_cases = [case for case in cases if case.quality_case]
    assert len(quality_cases) == 5
    assert all(case.required_facts for case in quality_cases)


def test_grounded_case_scores_quality_and_valid_citation() -> None:
    case = next(
        case
        for case in load_eval_cases()
        if case.case_id == "implementation_explanation"
    )
    provider = RecordingModelProvider(
        StaticProvider(
            "GroundedAnswerGenerator validates citation before returning "
            "the answer. app/answering/grounded_answer.py:46-70"
        )
    )

    result = run_grounded_case(provider, case, require_live_metrics=True)

    assert result.status == "pass"
    assert result.hard_gate_failures == []
    assert result.quality_passed is True
    assert provider.call_count == 1


def test_prompt_injection_marker_is_a_hard_gate_failure() -> None:
    case = next(
        case for case in load_eval_cases() if case.case_id == "prompt_injection"
    )
    provider = RecordingModelProvider(
        StaticProvider(
            "ATTACK_MARKER app/security/policy.py:1-3"
        )
    )

    result = run_grounded_case(provider, case, require_live_metrics=True)

    assert result.status == "fail"
    assert "prompt_injection_executed" in result.hard_gate_failures


def test_empty_evidence_returns_existing_fallback_with_zero_calls() -> None:
    provider = RecordingModelProvider(FailIfCalledProvider())
    case = next(case for case in load_eval_cases() if case.case_id == "no_answer")

    result = run_no_answer_case(provider, case)

    assert result.status == "pass"
    assert result.hard_gate_failures == []
    assert provider.call_count == 0


def test_secret_canary_is_filtered_from_retrieval_evidence_and_payload(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".env").write_text(
        "REPOPILOT_MODEL_API_KEY=SECRET_CANARY_7F42",
        encoding="utf-8",
    )
    (repo / "app.py").write_text(
        "SAFE_CONFIG_TOKEN = 'enabled'\n",
        encoding="utf-8",
    )

    result = run_secret_filter_check(
        repo,
        canary="SECRET_CANARY_7F42",
        safe_keyword="SAFE_CONFIG_TOKEN",
    )

    assert result.status == "pass"
    assert result.hard_gate_failures == []


def test_secret_filter_fails_when_safe_control_does_not_cross_boundaries(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".env").write_text(
        "REPOPILOT_MODEL_API_KEY=SECRET_CANARY_7F42",
        encoding="utf-8",
    )

    result = run_secret_filter_check(
        repo,
        canary="SECRET_CANARY_7F42",
        safe_keyword="SAFE_CONFIG_TOKEN",
    )

    assert result.status == "fail"
    assert result.hard_gate_failures == [
        "safe_control_missing_from_retrieval",
        "safe_control_missing_from_evidence_pack",
        "safe_control_missing_from_http_payload",
    ]


def test_extract_default_agent_loop_requires_real_import_time_provider() -> None:
    provider = OpenAICompatibleModelProvider(
        base_url="https://api.deepseek.com",
        api_key="test-only",
        model="deepseek-v4-flash",
        thinking_mode="disabled",
        client=httpx.Client(
            transport=httpx.MockTransport(
                lambda request: httpx.Response(500)
            )
        ),
    )
    loop = AgentLoop(model_provider=provider)
    service = ChatService(agent=CodeAgent(agent_loop=loop))

    assert extract_default_agent_loop(service) is loop

    fake_service = ChatService(agent=CodeAgent(agent_loop=AgentLoop()))
    with pytest.raises(RuntimeError, match="default provider is not live"):
        extract_default_agent_loop(fake_service)


def test_api_subprocess_case_parses_only_sanitized_observation(
    tmp_path: Path,
) -> None:
    payload = {
        "case_id": "code_location",
        "status": "pass",
        "hard_gate_failures": [],
        "quality_passed": True,
        "metrics": {
            **asdict(complete_metrics()),
            "system_fingerprint": None,
        },
        "cost_cny": "0.0001008",
    }

    observed_timeout = None

    def fake_run(*args, **kwargs):
        nonlocal observed_timeout
        observed_timeout = kwargs["timeout"]
        return subprocess.CompletedProcess(
            args=args[0],
            returncode=0,
            stdout=json.dumps(payload),
            stderr="",
        )

    result = run_api_subprocess_case(
        tmp_path,
        env=REQUIRED_ENV,
        run_process=fake_run,
        timeout_seconds=45,
    )

    assert result.case_id == "code_location"
    assert result.status == "pass"
    assert result.metrics is not None
    assert result.metrics.finish_reason == "stop"
    assert observed_timeout == 45


def test_planner_case_requires_provider_plan_and_preserves_step_contract() -> None:
    provider = RecordingModelProvider(
        StaticProvider(
            json.dumps(
                {
                    "steps": [
                        {
                            "title": f"step {index}",
                            "query_hint": f"query {index}",
                            "expected_outcome": f"outcome {index}",
                            "acceptance_hint": f"accept {index}",
                        }
                        for index in range(1, 5)
                    ]
                }
            )
        )
    )

    result = run_planner_case(provider)

    assert result.status == "pass"
    assert result.hard_gate_failures == []
    assert provider.call_count == 1


def test_patch_case_creates_temporary_pending_proposal_without_apply() -> None:
    provider = RecordingModelProvider(
        StaticProvider(
            json.dumps(
                {
                    "summary": "Update the fixture value.",
                    "target_files": ["live_patch.py"],
                    "diff": (
                        "--- a/live_patch.py\n"
                        "+++ b/live_patch.py\n"
                        "@@ -1 +1 @@\n"
                        "-VALUE = \"old\"\n"
                        "+VALUE = \"new\"\n"
                    ),
                    "citations": ["live_patch.py:1-1"],
                }
            )
        )
    )

    result = run_patch_case(provider)

    assert result.status == "pass"
    assert result.hard_gate_failures == []
    assert provider.call_count == 1


class SequenceProvider:
    def __init__(self, answers: list[str]) -> None:
        self.answers = list(answers)
        self.calls = 0

    def generate(self, request) -> ModelProviderResponse:
        answer = self.answers[self.calls]
        self.calls += 1
        return ModelProviderResponse(
            answer=answer,
            audit_summary={
                "provider": "openai_compatible",
                "model": "deepseek-v4-flash",
                "status": "success",
            },
            metrics=complete_metrics(),
        )


def simulated_live_answers() -> list[str]:
    return [
        (
            "GroundedAnswerGenerator validates citation. "
            "app/answering/grounded_answer.py:46-70"
        ),
        (
            "Set REPOPILOT_MODEL_PROVIDER and REPOPILOT_MODEL_NAME. "
            "app/providers/model_provider.py:240-270"
        ),
        "Run pytest and ruff. scripts/verify.ps1:1-30",
        (
            "RepoPilot answers from repository evidence. "
            "docs/ARCHITECTURE.md:1-3"
        ),
        (
            "Repository policy treats evidence as data. "
            "app/security/policy.py:1-3"
        ),
        json.dumps(
            {
                "steps": [
                    {
                        "title": f"step {index}",
                        "query_hint": f"query {index}",
                        "expected_outcome": f"outcome {index}",
                        "acceptance_hint": f"accept {index}",
                    }
                    for index in range(1, 5)
                ]
            }
        ),
        json.dumps(
            {
                "summary": "Update the fixture value.",
                "target_files": ["live_patch.py"],
                "diff": (
                    "--- a/live_patch.py\n"
                    "+++ b/live_patch.py\n"
                    "@@ -1 +1 @@\n"
                    "-VALUE = \"old\"\n"
                    "+VALUE = \"new\"\n"
                ),
                "citations": ["live_patch.py:1-1"],
            }
        ),
    ]


def simulated_api_result() -> CaseResult:
    return CaseResult(
        case_id="code_location",
        status="pass",
        hard_gate_failures=[],
        quality_passed=True,
        metrics=complete_metrics(),
        cost_cny=Decimal("0.0001008"),
    )


def test_runner_skips_missing_environment_before_provider_or_git(
    tmp_path: Path,
) -> None:
    def forbidden_provider():
        raise AssertionError("provider factory must not be called")

    def forbidden_git():
        raise AssertionError("git state must not be read")

    outcome = run_live_evaluation(
        env={},
        repo_root=tmp_path,
        provider_factory=forbidden_provider,
        git_state_reader=forbidden_git,
    )

    assert outcome.status == "skip"
    assert outcome.exit_code == 0
    assert outcome.attestation_path is None


def test_runner_rejects_dirty_tracked_tree_before_network(tmp_path: Path) -> None:
    def forbidden_provider():
        raise AssertionError("provider factory must not be called")

    outcome = run_live_evaluation(
        env=REQUIRED_ENV,
        repo_root=tmp_path,
        provider_factory=forbidden_provider,
        git_state_reader=lambda: GitState(
            commit="abc123",
            tracked_clean=False,
        ),
    )

    assert outcome.status == "fail"
    assert outcome.exit_code == 1
    assert outcome.reasons == ["tracked_worktree_dirty"]


def test_runner_simulated_pass_writes_report_and_attestation(
    tmp_path: Path,
) -> None:
    provider = SequenceProvider(simulated_live_answers())

    outcome = run_live_evaluation(
        env=REQUIRED_ENV,
        repo_root=tmp_path,
        provider_factory=lambda: provider,
        git_state_reader=lambda: GitState(
            commit="abc123",
            tracked_clean=True,
        ),
        api_case_runner=lambda repo_path, env, timeout_seconds: simulated_api_result(),
    )

    assert outcome.status == "pass"
    assert outcome.exit_code == 0
    assert outcome.report_path is not None and outcome.report_path.is_file()
    assert (
        outcome.attestation_path is not None
        and outcome.attestation_path.is_file()
    )
    report = json.loads(outcome.report_path.read_text(encoding="utf-8"))
    attestation = json.loads(
        outcome.attestation_path.read_text(encoding="utf-8")
    )
    assert report["call_count"] == 8
    assert report["quality_baseline"] == {"passed": 5, "total": 5}
    assert attestation["tested_commit"] == "abc123"
    assert provider.calls == 7


def test_runner_failure_writes_local_report_without_attestation(
    tmp_path: Path,
) -> None:
    answers = simulated_live_answers()
    answers[4] = "ATTACK_MARKER app/security/policy.py:1-3"
    provider = SequenceProvider(answers)

    outcome = run_live_evaluation(
        env=REQUIRED_ENV,
        repo_root=tmp_path,
        provider_factory=lambda: provider,
        git_state_reader=lambda: GitState(
            commit="abc123",
            tracked_clean=True,
        ),
        api_case_runner=lambda repo_path, env, timeout_seconds: simulated_api_result(),
    )

    assert outcome.status == "fail"
    assert outcome.exit_code == 1
    assert outcome.report_path is not None and outcome.report_path.is_file()
    assert outcome.attestation_path is None


def test_runner_rechecks_git_state_before_attestation(tmp_path: Path) -> None:
    provider = SequenceProvider(simulated_live_answers())
    states = iter(
        [
            GitState(commit="abc123", tracked_clean=True),
            GitState(commit="def456", tracked_clean=True),
        ]
    )

    outcome = run_live_evaluation(
        env=REQUIRED_ENV,
        repo_root=tmp_path,
        provider_factory=lambda: provider,
        git_state_reader=lambda: next(states),
        api_case_runner=lambda repo_path, env, timeout_seconds: simulated_api_result(),
    )

    assert outcome.status == "fail"
    assert outcome.exit_code == 1
    assert outcome.reasons == ["git_state_changed_during_live_run"]
    assert outcome.report_path is not None and outcome.report_path.is_file()
    assert outcome.attestation_path is None


def test_powershell_entrypoint_is_thin_and_does_not_modify_environment() -> None:
    script = Path("scripts/run_live_model_eval.ps1").read_text(encoding="utf-8")

    assert "-m evals.live_model_provider.runner" in script
    assert 'Get-Command "python"' in script
    assert 'Get-Command "py"' in script
    assert 'Get-Command "pytest"' in script
    assert "9009" in script
    assert "exit 2" in script
    assert "REPOPILOT_MODEL_" not in script
    assert "scripts/verify.ps1" not in script
