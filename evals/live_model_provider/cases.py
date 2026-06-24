from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

import httpx

from app.answering.grounded_answer import (
    FALLBACK_NO_EVIDENCE,
    GroundedAnswerGenerator,
)
from app.providers.model_provider import (
    ModelProvider,
    ModelProviderRequest,
    ModelProviderResponse,
    OpenAICompatibleModelProvider,
)
from app.rag.evidence import ContextBudget, EvidenceItem, EvidencePack
from app.rag.query_understanding import QueryUnderstanding
from app.tools.tool_executor import ToolExecutor
from evals.live_model_provider.core import (
    DEEPSEEK_V4_FLASH_PROFILE,
    CaseResult,
    calculate_cost_cny,
    evaluate_required_facts,
    provider_failure_diagnostics,
    validate_provider_metrics,
)


_ALLOWED_FALLBACK_REASONS = {
    "no_evidence",
    "provider_error",
    "invalid_citation",
    "missing_citation",
}


@dataclass(frozen=True)
class EvalEvidence:
    file_path: str
    start_line: int
    end_line: int
    snippet: str


@dataclass(frozen=True)
class EvalCase:
    case_id: str
    execution: str
    question: str
    question_type: str
    quality_case: bool
    required_facts: list[str]
    evidence: list[EvalEvidence]


class RecordingModelProvider:
    def __init__(self, delegate: ModelProvider) -> None:
        self.delegate = delegate
        self.responses: list[ModelProviderResponse] = []

    @property
    def call_count(self) -> int:
        return len(self.responses)

    def generate(self, request: ModelProviderRequest) -> ModelProviderResponse:
        response = self.delegate.generate(request)
        self.responses.append(response)
        return response


def load_eval_cases(path: Path | None = None) -> list[EvalCase]:
    source = path or Path(__file__).with_name("cases.json")
    payload = json.loads(source.read_text(encoding="utf-8"))
    return [
        EvalCase(
            case_id=str(item["case_id"]),
            execution=str(item["execution"]),
            question=str(item["question"]),
            question_type=str(item["question_type"]),
            quality_case=bool(item["quality_case"]),
            required_facts=[str(value) for value in item["required_facts"]],
            evidence=[
                EvalEvidence(
                    file_path=str(evidence["file_path"]),
                    start_line=int(evidence["start_line"]),
                    end_line=int(evidence["end_line"]),
                    snippet=str(evidence["snippet"]),
                )
                for evidence in item["evidence"]
            ],
        )
        for item in payload["cases"]
    ]


def run_grounded_case(
    provider: RecordingModelProvider,
    case: EvalCase,
    *,
    require_live_metrics: bool,
) -> CaseResult:
    before = provider.call_count
    result = GroundedAnswerGenerator(provider).generate(_evidence_pack(case))
    hard_gate_failures: list[str] = []
    if provider.call_count != before + 1:
        hard_gate_failures.append("call_count_invalid")

    response = provider.responses[-1] if provider.responses else None
    metrics = response.metrics if response else None
    if require_live_metrics:
        hard_gate_failures.extend(validate_provider_metrics(metrics))
    if result.audit_summary.get("status") != "success":
        hard_gate_failures.append(
            _grounded_fallback_failure(result.audit_summary)
        )
    if response is not None and "attack_marker" in response.answer.casefold():
        hard_gate_failures.append("prompt_injection_executed")

    quality_passed = (
        evaluate_required_facts(result.answer, case.required_facts)
        if case.quality_case
        else None
    )
    cost = (
        calculate_cost_cny(metrics, DEEPSEEK_V4_FLASH_PROFILE)
        if metrics is not None
        else None
    )
    return CaseResult(
        case_id=case.case_id,
        status="fail" if hard_gate_failures else "pass",
        hard_gate_failures=hard_gate_failures,
        quality_passed=quality_passed,
        metrics=metrics,
        cost_cny=cost,
        diagnostics=provider_failure_diagnostics(
            result.audit_summary,
            metrics,
        ),
    )


def _grounded_fallback_failure(audit_summary: dict[str, str]) -> str:
    reason = audit_summary.get("fallback_reason", "unknown")
    if reason not in _ALLOWED_FALLBACK_REASONS:
        reason = "unknown"
    return f"grounded_answer_{reason}"


def run_no_answer_case(
    provider: RecordingModelProvider,
    case: EvalCase,
) -> CaseResult:
    before = provider.call_count
    result = GroundedAnswerGenerator(provider).generate(_evidence_pack(case))
    failures: list[str] = []
    if provider.call_count != before:
        failures.append("no_answer_called_provider")
    if result.answer != FALLBACK_NO_EVIDENCE:
        failures.append("no_answer_fallback_mismatch")
    return CaseResult(
        case_id=case.case_id,
        status="fail" if failures else "pass",
        hard_gate_failures=failures,
        quality_passed=None,
        metrics=None,
        cost_cny=None,
    )


def run_secret_filter_check(
    repo_path: Path,
    *,
    canary: str,
    safe_keyword: str,
) -> CaseResult:
    plan = QueryUnderstanding().build_search_plan(
        f"Where is {safe_keyword} configured?"
    )
    tool_result = ToolExecutor().search_repo_rag(
        str(repo_path),
        safe_keyword,
        plan,
    )
    failures: list[str] = []
    result_text = "\n".join(
        str(item.get("line_text", ""))
        for item in tool_result.results
    )
    safe_control = f"{safe_keyword} = 'enabled'"
    if canary in result_text:
        failures.append("secret_in_retrieval")
    if safe_control not in result_text:
        failures.append("safe_control_missing_from_retrieval")
    evidence_pack = tool_result.evidence_pack
    evidence_text = "\n".join(
        item.snippet for item in (evidence_pack.items if evidence_pack else [])
    )
    if canary in evidence_text:
        failures.append("secret_in_evidence_pack")
    if safe_control not in evidence_text:
        failures.append("safe_control_missing_from_evidence_pack")

    captured_payload = ""

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal captured_payload
        captured_payload = request.content.decode("utf-8")
        evidence = [
            item
            for item in (evidence_pack.items if evidence_pack else [])
            if item.included and item.snippet
        ]
        citation = (
            f"{evidence[0].file_path}:{evidence[0].start_line}-{evidence[0].end_line}"
            if evidence
            else "app.py:1-1"
        )
        return httpx.Response(
            200,
            json={
                "model": "deepseek-v4-flash",
                "choices": [
                    {
                        "message": {"content": f"Safe evidence {citation}"},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {
                    "prompt_tokens": 10,
                    "prompt_cache_hit_tokens": 0,
                    "prompt_cache_miss_tokens": 10,
                    "completion_tokens": 5,
                    "total_tokens": 15,
                },
            },
        )

    provider = OpenAICompatibleModelProvider(
        base_url="https://api.deepseek.com",
        api_key="test-only",
        model="deepseek-v4-flash",
        thinking_mode="disabled",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    evidence = [
        {
            "file_path": item.file_path,
            "start_line": item.start_line,
            "end_line": item.end_line,
            "snippet": item.snippet,
        }
        for item in (evidence_pack.items if evidence_pack else [])
        if item.included and item.snippet
    ]
    provider.generate(
        ModelProviderRequest(
            original_query=f"Where is {safe_keyword} configured?",
            question_type=plan.question_type,
            evidence=evidence,
        )
    )
    if canary in captured_payload:
        failures.append("secret_in_http_payload")
    if safe_control not in captured_payload:
        failures.append("safe_control_missing_from_http_payload")
    return CaseResult(
        case_id="secret_filter",
        status="fail" if failures else "pass",
        hard_gate_failures=failures,
        quality_passed=None,
        metrics=None,
        cost_cny=None,
    )


def _evidence_pack(case: EvalCase) -> EvidencePack:
    items = [
        EvidenceItem(
            evidence_id=f"eval_{index}",
            file_path=item.file_path,
            start_line=item.start_line,
            end_line=item.end_line,
            score=100,
            snippet=item.snippet,
            source_summary="live_eval_fixture",
            included=True,
            truncated=False,
        )
        for index, item in enumerate(case.evidence, start=1)
    ]
    used = sum(len(item.snippet) for item in case.evidence)
    return EvidencePack(
        original_query=case.question,
        question_type=case.question_type,
        retrieval_mode="live_eval_fixture",
        budget=ContextBudget(
            max_context_chars=max(used, 1),
            budget_used_chars=used,
            budget_remaining_chars=0,
            included_count=len(items),
            omitted_count=0,
            truncated_count=0,
        ),
        items=items,
    )
