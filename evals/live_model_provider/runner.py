from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
import os
from pathlib import Path
import subprocess
import tempfile
from time import monotonic
from typing import Callable, Mapping

import httpx

from app.providers.model_provider import ModelProvider, OpenAICompatibleModelProvider
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
from evals.live_model_provider.core import (
    DEEPSEEK_V4_FLASH_PROFILE,
    EXIT_ERROR,
    EXIT_FAIL,
    EXIT_SKIP,
    RUBRIC_VERSION,
    CallBudget,
    CaseResult,
    LiveEvalReport,
    write_attestation,
    write_local_report,
    validate_live_environment,
)


MAX_LIVE_CALLS = 8
RUN_TIMEOUT_SECONDS = 300


@dataclass(frozen=True)
class GitState:
    commit: str
    tracked_clean: bool


@dataclass(frozen=True)
class LiveEvaluationOutcome:
    status: str
    exit_code: int
    reasons: list[str] = field(default_factory=list)
    report_path: Path | None = None
    attestation_path: Path | None = None


def run_live_evaluation(
    *,
    env: Mapping[str, str],
    repo_root: Path,
    provider_factory: Callable[[], ModelProvider] | None = None,
    git_state_reader: Callable[[], GitState] | None = None,
    api_case_runner: Callable[..., CaseResult] = run_api_subprocess_case,
) -> LiveEvaluationOutcome:
    environment = validate_live_environment(
        env,
        DEEPSEEK_V4_FLASH_PROFILE,
    )
    if environment.status != "ready":
        return LiveEvaluationOutcome(
            status=environment.status,
            exit_code=environment.exit_code,
            reasons=environment.reasons,
        )

    read_git = git_state_reader or (lambda: _read_git_state(repo_root))
    git_state = read_git()
    if not git_state.tracked_clean:
        return LiveEvaluationOutcome(
            status="fail",
            exit_code=EXIT_FAIL,
            reasons=["tracked_worktree_dirty"],
        )

    started_at = _utc_timestamp()
    started_clock = monotonic()
    budget = CallBudget(max_calls=MAX_LIVE_CALLS)
    results: list[CaseResult] = []

    factory = provider_factory or (lambda: _provider_from_env(env))
    provider = RecordingModelProvider(factory())
    cases = {case.case_id: case for case in load_eval_cases()}

    with tempfile.TemporaryDirectory(prefix="repopilot-live-api-") as temp:
        budget.consume("code_location")
        results.append(
            api_case_runner(
                Path(temp),
                env={
                    **dict(env),
                    "REPOPILOT_MODEL_TIMEOUT_SECONDS": "30",
                },
                timeout_seconds=min(120, _remaining_seconds(started_clock)),
            )
        )

    for case_id in (
        "implementation_explanation",
        "configuration",
        "test_validation",
        "ambiguous",
        "prompt_injection",
    ):
        if _deadline_exceeded(started_clock):
            results.append(_deadline_case(case_id))
            break
        _apply_remaining_timeout(provider.delegate, started_clock)
        budget.consume(case_id)
        results.append(
            run_grounded_case(
                provider,
                cases[case_id],
                require_live_metrics=True,
            )
        )

    results.append(run_no_answer_case(provider, cases["no_answer"]))

    if not _deadline_exceeded(started_clock):
        _apply_remaining_timeout(provider.delegate, started_clock)
        budget.consume("planner")
        results.append(run_planner_case(provider))
    else:
        results.append(_deadline_case("planner"))

    if not _deadline_exceeded(started_clock):
        _apply_remaining_timeout(provider.delegate, started_clock)
        budget.consume("patch")
        results.append(run_patch_case(provider))
    else:
        results.append(_deadline_case("patch"))

    with tempfile.TemporaryDirectory(prefix="repopilot-live-secret-") as temp:
        secret_repo = Path(temp)
        (secret_repo / ".env").write_text(
            "REPOPILOT_MODEL_API_KEY=SECRET_CANARY_7F42",
            encoding="utf-8",
        )
        (secret_repo / "app.py").write_text(
            "SAFE_CONFIG_TOKEN = 'enabled'\n",
            encoding="utf-8",
        )
        results.append(
            run_secret_filter_check(
                secret_repo,
                canary="SECRET_CANARY_7F42",
                safe_keyword="SAFE_CONFIG_TOKEN",
            )
        )

    api_result = next(
        (result for result in results if result.case_id == "code_location"),
        None,
    )
    observed_calls = provider.call_count + (
        1
        if api_result is not None and api_result.metrics is not None
        else 0
    )
    observed_call_count_invalid = (
        api_result is not None
        and api_result.metrics is not None
        and observed_calls != MAX_LIVE_CALLS
    )
    if budget.used != MAX_LIVE_CALLS or observed_call_count_invalid:
        results.append(
            CaseResult(
                case_id="call_budget",
                status="fail",
                hard_gate_failures=["live_call_count_invalid"],
                quality_passed=None,
                metrics=None,
                cost_cny=None,
            )
        )

    final_git_state = read_git()
    if (
        not final_git_state.tracked_clean
        or final_git_state.commit != git_state.commit
    ):
        results.append(
            CaseResult(
                case_id="git_state",
                status="fail",
                hard_gate_failures=["git_state_changed_during_live_run"],
                quality_passed=None,
                metrics=None,
                cost_cny=None,
            )
        )

    completed_at = _utc_timestamp()
    quality_results = [
        result
        for result in results
        if result.quality_passed is not None
    ]
    status = (
        "pass"
        if all(result.status == "pass" for result in results)
        else "fail"
    )
    report = LiveEvalReport(
        status=status,
        tested_commit=git_state.commit,
        started_at=started_at,
        completed_at=completed_at,
        profile=DEEPSEEK_V4_FLASH_PROFILE,
        rubric_version=RUBRIC_VERSION,
        call_count=observed_calls,
        quality_passed=sum(
            result.quality_passed is True for result in quality_results
        ),
        quality_total=len(quality_results),
        cases=results,
    )
    report_path, digest = write_local_report(
        report,
        repo_root / ".repopilot",
    )
    if status != "pass":
        return LiveEvaluationOutcome(
            status="fail",
            exit_code=EXIT_FAIL,
            reasons=[
                failure
                for result in results
                for failure in result.hard_gate_failures
            ],
            report_path=report_path,
        )

    attestation_path = write_attestation(
        report,
        local_report_sha256=digest,
        docs_root=repo_root / "docs" / "evals" / "live-model-provider",
    )
    return LiveEvaluationOutcome(
        status="pass",
        exit_code=EXIT_SKIP,
        report_path=report_path,
        attestation_path=attestation_path,
    )


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    try:
        outcome = run_live_evaluation(
            env=os.environ,
            repo_root=repo_root,
        )
    except Exception as exc:
        print(f"ERROR live model provider eval: {type(exc).__name__}")
        return EXIT_ERROR

    detail = ",".join(outcome.reasons)
    if outcome.status == "skip":
        print(f"SKIP live model provider eval: {detail}")
    elif outcome.status == "fail":
        print(f"FAIL live model provider eval: {detail}")
        if outcome.report_path:
            print(f"report={outcome.report_path}")
    else:
        print("PASS live model provider eval")
        print(f"report={outcome.report_path}")
        print(f"attestation={outcome.attestation_path}")
    return outcome.exit_code


def _provider_from_env(env: Mapping[str, str]) -> OpenAICompatibleModelProvider:
    return OpenAICompatibleModelProvider(
        base_url=str(env["REPOPILOT_MODEL_BASE_URL"]).strip(),
        api_key=str(env["REPOPILOT_MODEL_API_KEY"]).strip(),
        model=str(env["REPOPILOT_MODEL_NAME"]).strip(),
        timeout_seconds=30,
        thinking_mode=str(env["REPOPILOT_MODEL_THINKING"]).strip(),
    )


def _read_git_state(repo_root: Path) -> GitState:
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    status = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=no"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    return GitState(commit=commit, tracked_clean=not status)


def _deadline_exceeded(started_clock: float) -> bool:
    return monotonic() - started_clock >= RUN_TIMEOUT_SECONDS


def _remaining_seconds(started_clock: float) -> float:
    return max(0.1, RUN_TIMEOUT_SECONDS - (monotonic() - started_clock))


def _apply_remaining_timeout(provider: object, started_clock: float) -> None:
    if not isinstance(provider, OpenAICompatibleModelProvider):
        return
    timeout = min(30.0, _remaining_seconds(started_clock))
    provider.timeout_seconds = timeout
    provider.client.timeout = httpx.Timeout(timeout)


def _deadline_case(case_id: str) -> CaseResult:
    return CaseResult(
        case_id=case_id,
        status="fail",
        hard_gate_failures=["run_timeout"],
        quality_passed=None,
        metrics=None,
        cost_cny=None,
    )


def _utc_timestamp() -> str:
    return datetime.now(tz=UTC).isoformat(timespec="seconds").replace(
        "+00:00",
        "Z",
    )


if __name__ == "__main__":
    raise SystemExit(main())
