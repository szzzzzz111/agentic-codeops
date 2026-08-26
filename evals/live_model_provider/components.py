from __future__ import annotations

import gc
import json
import os
import subprocess
import sys
import tempfile
from collections.abc import Callable, Mapping
from pathlib import Path

from app.longtask.planner import PLAN_SOURCE_PROVIDER, LongTaskPlanner
from app.patching.manager import PatchManager
from app.patching.provider import ModelPatchAuthoringProvider
from app.rag.evidence import ContextBudget, EvidenceItem, EvidencePack
from evals.live_model_provider.cases import RecordingModelProvider
from evals.live_model_provider.core import (
    DEEPSEEK_V4_FLASH_PROFILE,
    CaseResult,
    calculate_cost_cny,
    deserialize_case_result,
    provider_failure_diagnostics,
    validate_provider_metrics,
)

ProcessRunner = Callable[..., subprocess.CompletedProcess[str]]


def run_api_subprocess_case(
    repo_path: Path,
    *,
    env: Mapping[str, str],
    run_process: ProcessRunner = subprocess.run,
    timeout_seconds: float = 120,
) -> CaseResult:
    repo_path.mkdir(parents=True, exist_ok=True)
    (repo_path / "live_target.py").write_text(
        "UNIQUE_LIVE_LOCATION_TOKEN = 'ready'\n"
        "\n"
        "def locate_live_target():\n"
        "    return UNIQUE_LIVE_LOCATION_TOKEN\n",
        encoding="utf-8",
    )
    command = [
        sys.executable,
        "-m",
        "evals.live_model_provider.api_smoke",
        "--repo",
        str(repo_path),
    ]
    try:
        completed = run_process(
            command,
            cwd=str(Path(__file__).resolve().parents[2]),
            env={**os.environ, **dict(env)},
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return _failed_case("code_location", "api_subprocess_timeout")
    if completed.returncode != 0:
        return _failed_case("code_location", "api_subprocess_error")
    try:
        payload = json.loads(completed.stdout)
        return deserialize_case_result(payload)
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        return _failed_case("code_location", "api_subprocess_invalid_output")


def run_planner_case(provider: RecordingModelProvider) -> CaseResult:
    before = provider.call_count
    plan = LongTaskPlanner(
        provider=provider,
        provider_enabled=True,
    ).plan("Explain how the model provider integration works.")
    failures: list[str] = []
    if provider.call_count != before + 1:
        failures.append("planner_call_count_invalid")
    if plan.plan_source != PLAN_SOURCE_PROVIDER or plan.provider_status != "success":
        failures.append("planner_fallback")
    if not 3 <= len(plan.steps) <= 5:
        failures.append("planner_step_count_invalid")
    if [step.step_id for step in plan.steps] != [
        f"step_{index}" for index in range(1, len(plan.steps) + 1)
    ]:
        failures.append("planner_step_order_invalid")
    if any(step.action_type != "repo_rag" for step in plan.steps):
        failures.append("planner_action_type_invalid")
    response = provider.responses[-1] if provider.responses else None
    metrics = response.metrics if response else None
    failures.extend(validate_provider_metrics(metrics))
    return _case_with_metrics("planner", failures, metrics, response)


def run_patch_case(provider: RecordingModelProvider) -> CaseResult:
    before = provider.call_count
    failures: list[str] = []
    with tempfile.TemporaryDirectory(prefix="repopilot-live-patch-") as temp:
        repo = Path(temp)
        target = repo / "live_patch.py"
        target.write_text('VALUE = "old"\n', encoding="utf-8")
        evidence_pack = EvidencePack(
            original_query='Change VALUE from "old" to "new" in live_patch.py.',
            question_type="implementation_explanation",
            retrieval_mode="live_eval_fixture",
            budget=ContextBudget(
                max_context_chars=13,
                budget_used_chars=13,
                budget_remaining_chars=0,
                included_count=1,
                omitted_count=0,
                truncated_count=0,
            ),
            items=[
                EvidenceItem(
                    evidence_id="eval_patch",
                    file_path="live_patch.py",
                    start_line=1,
                    end_line=1,
                    score=100,
                    snippet='VALUE = "old"',
                    source_summary="live_eval_fixture",
                    included=True,
                    truncated=False,
                )
            ],
        )
        manager = PatchManager(
            provider=ModelPatchAuthoringProvider(provider)
        )
        result = manager.propose_patch(
            user_id="live-eval",
            repo_path=str(repo),
            message=evidence_pack.original_query,
            evidence_pack=evidence_pack,
        )
        if provider.call_count != before + 1:
            failures.append("patch_call_count_invalid")
        if not result.patch_id:
            failures.append("patch_proposal_invalid")
        if target.read_text(encoding="utf-8") != 'VALUE = "old"\n':
            failures.append("patch_was_applied")
        if result.patch_id and not (repo / ".repopilot" / "patches.sqlite3").is_file():
            failures.append("patch_pending_store_missing")
        gc.collect()

    response = provider.responses[-1] if provider.responses else None
    metrics = response.metrics if response else None
    failures.extend(validate_provider_metrics(metrics))
    return _case_with_metrics("patch", failures, metrics, response)


def _case_with_metrics(
    case_id: str,
    failures: list[str],
    metrics,
    response=None,
) -> CaseResult:
    cost = (
        calculate_cost_cny(metrics, DEEPSEEK_V4_FLASH_PROFILE)
        if metrics is not None
        else None
    )
    return CaseResult(
        case_id=case_id,
        status="fail" if failures else "pass",
        hard_gate_failures=failures,
        quality_passed=None,
        metrics=metrics,
        cost_cny=cost,
        diagnostics=(
            provider_failure_diagnostics(response.audit_summary, metrics)
            if response is not None
            else None
        ),
    )


def _failed_case(case_id: str, failure: str) -> CaseResult:
    return CaseResult(
        case_id=case_id,
        status="fail",
        hard_gate_failures=[failure],
        quality_passed=False if case_id == "code_location" else None,
        metrics=None,
        cost_cny=None,
    )
