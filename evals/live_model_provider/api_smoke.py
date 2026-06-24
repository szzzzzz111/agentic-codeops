from __future__ import annotations

import argparse
import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.harness.kernel import AgentLoop
from app.providers.model_provider import OpenAICompatibleModelProvider
from app.services.chat_service import ChatService
from evals.live_model_provider.cases import RecordingModelProvider
from evals.live_model_provider.core import (
    DEEPSEEK_V4_FLASH_PROFILE,
    CaseResult,
    calculate_cost_cny,
    evaluate_required_facts,
    provider_failure_diagnostics,
    serialize_case_result,
    validate_provider_metrics,
)


def extract_default_agent_loop(chat_service: ChatService) -> AgentLoop:
    agent = getattr(chat_service, "_agent", None)
    loop = getattr(agent, "_agent_loop", None)
    if not isinstance(loop, AgentLoop):
        raise RuntimeError("default AgentLoop unavailable")
    provider = getattr(loop.grounded_answer, "provider", None)
    if not isinstance(provider, OpenAICompatibleModelProvider):
        raise RuntimeError("default provider is not live")
    return loop


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    args = parser.parse_args()

    from app.api import chat as chat_module
    from app.main import app

    loop = extract_default_agent_loop(chat_module.chat_service)
    original_provider = loop.grounded_answer.provider
    recorder = RecordingModelProvider(original_provider)
    loop.grounded_answer.provider = recorder

    response = TestClient(app).post(
        "/chat",
        json={
            "user_id": "live-eval",
            "session_id": "live-eval",
            "message": "Where is UNIQUE_LIVE_LOCATION_TOKEN implemented?",
            "repo_path": str(Path(args.repo).resolve()),
        },
    )
    failures: list[str] = []
    if response.status_code != 200:
        failures.append("chat_status_invalid")
        body: dict[str, object] = {}
    else:
        body = response.json()
    if set(body) != {"trace_id", "answer", "related_files", "tool_calls"}:
        failures.append("chat_contract_invalid")
    answer = str(body.get("answer", ""))
    if "live_target.py:" not in answer:
        failures.append("chat_citation_invalid")
    if recorder.call_count != 1:
        failures.append("chat_call_count_invalid")
    provider_response = recorder.responses[-1] if recorder.responses else None
    metrics = provider_response.metrics if provider_response else None
    failures.extend(validate_provider_metrics(metrics))
    quality_passed = evaluate_required_facts(
        answer,
        ["live_target.py", "locate_live_target"],
    )
    cost = (
        calculate_cost_cny(metrics, DEEPSEEK_V4_FLASH_PROFILE)
        if metrics is not None
        else None
    )
    result = CaseResult(
        case_id="code_location",
        status="fail" if failures else "pass",
        hard_gate_failures=failures,
        quality_passed=quality_passed,
        metrics=metrics,
        cost_cny=cost,
        diagnostics=(
            provider_failure_diagnostics(
                provider_response.audit_summary,
                metrics,
            )
            if provider_response is not None
            else None
        ),
    )
    print(json.dumps(serialize_case_result(result), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
