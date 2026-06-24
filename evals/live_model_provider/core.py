from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
import hashlib
import json
from pathlib import Path
from typing import Mapping

from app.providers.model_provider import ProviderCallMetrics


EXIT_SKIP = 0
EXIT_FAIL = 1
EXIT_ERROR = 2
RUBRIC_VERSION = "2026-06-22"
EXPECTED_LIVE_CALLS = 8
EXPECTED_LIVE_CASE_IDS = frozenset(
    {
        "code_location",
        "implementation_explanation",
        "configuration",
        "test_validation",
        "ambiguous",
        "prompt_injection",
        "no_answer",
        "planner",
        "patch",
        "secret_filter",
    }
)
REQUIRED_PROVIDER_CASE_IDS = frozenset(
    {
        "code_location",
        "implementation_explanation",
        "configuration",
        "test_validation",
        "ambiguous",
        "prompt_injection",
        "planner",
        "patch",
    }
)
REQUIRED_ENV_NAMES = (
    "REPOPILOT_MODEL_PROVIDER",
    "REPOPILOT_MODEL_BASE_URL",
    "REPOPILOT_MODEL_API_KEY",
    "REPOPILOT_MODEL_NAME",
    "REPOPILOT_MODEL_THINKING",
)
LIVE_NETWORK_CONFIRMATION_ENV = "REPOPILOT_LIVE_NETWORK_CONFIRMED"
CONFORMANCE_FAILURE_GATES = frozenset(
    {
        "chat_citation_invalid",
        "chat_contract_invalid",
        "chat_status_invalid",
        "finish_reason_not_stop",
        "grounded_answer_invalid_citation",
        "grounded_answer_missing_citation",
        "grounded_answer_no_evidence",
        "grounded_answer_provider_error",
        "grounded_answer_unknown",
        "metrics_missing",
        "no_answer_called_provider",
        "no_answer_fallback_mismatch",
        "patch_pending_store_missing",
        "patch_proposal_invalid",
        "patch_was_applied",
        "planner_action_type_invalid",
        "planner_fallback",
        "planner_step_count_invalid",
        "planner_step_order_invalid",
        "prompt_injection_executed",
        "prompt_token_split_mismatch",
        "requested_model_mismatch",
        "returned_model_mismatch",
        "safe_control_missing_from_evidence_pack",
        "safe_control_missing_from_http_payload",
        "safe_control_missing_from_retrieval",
        "secret_in_evidence_pack",
        "secret_in_http_payload",
        "secret_in_retrieval",
        "total_token_count_mismatch",
        "usage_incomplete",
        "usage_negative",
    }
)
INTEGRITY_FAILURE_GATES = frozenset(
    {
        "api_subprocess_error",
        "api_subprocess_invalid_output",
        "api_subprocess_timeout",
        "call_count_invalid",
        "chat_call_count_invalid",
        "git_state_changed_during_live_run",
        "live_call_count_invalid",
        "patch_call_count_invalid",
        "planner_call_count_invalid",
        "run_timeout",
    }
)


class EvaluationIntegrityError(ValueError):
    pass


@dataclass(frozen=True)
class Pricing:
    effective_date: str
    cache_hit_cny_per_million: Decimal
    cache_miss_cny_per_million: Decimal
    output_cny_per_million: Decimal


@dataclass(frozen=True)
class ProviderProfile:
    profile_id: str
    version: str
    provider: str
    base_url: str
    model: str
    thinking: str
    pricing: Pricing


DEEPSEEK_V4_FLASH_PROFILE = ProviderProfile(
    profile_id="deepseek-v4-flash",
    version="2026-06-22",
    provider="openai_compatible",
    base_url="https://api.deepseek.com",
    model="deepseek-v4-flash",
    thinking="disabled",
    pricing=Pricing(
        effective_date="2026-06-22",
        cache_hit_cny_per_million=Decimal("0.02"),
        cache_miss_cny_per_million=Decimal("1"),
        output_cny_per_million=Decimal("2"),
    ),
)


@dataclass(frozen=True)
class EnvironmentValidation:
    status: str
    exit_code: int
    reasons: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class CaseResult:
    case_id: str
    status: str
    hard_gate_failures: list[str]
    quality_passed: bool | None
    metrics: ProviderCallMetrics | None
    cost_cny: Decimal | None
    diagnostics: dict[str, str] | None = None


@dataclass(frozen=True)
class LiveEvalReport:
    status: str
    tested_commit: str
    started_at: str
    completed_at: str
    profile: ProviderProfile
    rubric_version: str
    call_count: int
    quality_passed: int
    quality_total: int
    cases: list[CaseResult]


class CallBudget:
    def __init__(self, *, max_calls: int) -> None:
        self.max_calls = max_calls
        self._case_ids: set[str] = set()

    @property
    def used(self) -> int:
        return len(self._case_ids)

    def consume(self, case_id: str) -> None:
        if case_id in self._case_ids:
            raise ValueError("case already called")
        if self.used >= self.max_calls:
            raise ValueError("live call budget exceeded")
        self._case_ids.add(case_id)


def validate_live_environment(
    env: Mapping[str, str],
    profile: ProviderProfile,
) -> EnvironmentValidation:
    missing = [
        name
        for name in REQUIRED_ENV_NAMES
        if not str(env.get(name, "")).strip()
    ]
    if missing:
        return EnvironmentValidation(
            status="skip",
            exit_code=EXIT_SKIP,
            reasons=[f"missing:{name}" for name in missing],
        )

    expected = {
        "REPOPILOT_MODEL_PROVIDER": profile.provider,
        "REPOPILOT_MODEL_BASE_URL": profile.base_url,
        "REPOPILOT_MODEL_NAME": profile.model,
        "REPOPILOT_MODEL_THINKING": profile.thinking,
    }
    mismatched = [
        name
        for name, expected_value in expected.items()
        if str(env.get(name, "")).strip() != expected_value
    ]
    if mismatched:
        return EnvironmentValidation(
            status="fail",
            exit_code=EXIT_FAIL,
            reasons=[f"profile_mismatch:{name}" for name in mismatched],
        )
    return EnvironmentValidation(status="ready", exit_code=EXIT_SKIP)


def validate_provider_metrics(metrics: ProviderCallMetrics | None) -> list[str]:
    if metrics is None:
        return ["metrics_missing", "usage_incomplete"]
    failures: list[str] = []
    if metrics.finish_reason != "stop":
        failures.append("finish_reason_not_stop")
    if metrics.requested_model != DEEPSEEK_V4_FLASH_PROFILE.model:
        failures.append("requested_model_mismatch")
    if metrics.returned_model != DEEPSEEK_V4_FLASH_PROFILE.model:
        failures.append("returned_model_mismatch")
    required_usage = (
        metrics.prompt_tokens,
        metrics.prompt_cache_hit_tokens,
        metrics.prompt_cache_miss_tokens,
        metrics.completion_tokens,
        metrics.total_tokens,
    )
    if any(value is None for value in required_usage):
        failures.append("usage_incomplete")
    elif any(value < 0 for value in required_usage):
        failures.append("usage_negative")
    else:
        assert metrics.prompt_tokens is not None
        assert metrics.prompt_cache_hit_tokens is not None
        assert metrics.prompt_cache_miss_tokens is not None
        assert metrics.completion_tokens is not None
        assert metrics.total_tokens is not None
        if (
            metrics.prompt_cache_hit_tokens
            + metrics.prompt_cache_miss_tokens
            != metrics.prompt_tokens
        ):
            failures.append("prompt_token_split_mismatch")
        if (
            metrics.prompt_tokens + metrics.completion_tokens
            != metrics.total_tokens
        ):
            failures.append("total_token_count_mismatch")
    return failures


def has_evaluable_provider_contact(metrics: ProviderCallMetrics | None) -> bool:
    if metrics is None or metrics.availability != "available":
        return False
    required_usage = (
        metrics.prompt_tokens,
        metrics.prompt_cache_hit_tokens,
        metrics.prompt_cache_miss_tokens,
        metrics.completion_tokens,
        metrics.total_tokens,
    )
    return (
        metrics.finish_reason is not None
        and metrics.returned_model is not None
        and all(value is not None for value in required_usage)
    )


def provider_failure_diagnostics(
    audit_summary: Mapping[str, str],
    metrics: ProviderCallMetrics | None,
) -> dict[str, str] | None:
    if metrics is None or metrics.availability != "unavailable":
        return None
    error_class = _diagnostic_code(
        str(audit_summary.get("error_class", "")).strip()
    )
    if not error_class:
        return None
    status_class = _status_class_for_error(error_class)
    return {
        "phase": _phase_for_status_class(status_class),
        "error_class": error_class,
        "status_class": status_class,
    }


def calculate_cost_cny(
    metrics: ProviderCallMetrics,
    profile: ProviderProfile,
) -> Decimal | None:
    if validate_provider_metrics(metrics):
        return None
    million = Decimal(1_000_000)
    assert metrics.prompt_cache_hit_tokens is not None
    assert metrics.prompt_cache_miss_tokens is not None
    assert metrics.completion_tokens is not None
    return (
        Decimal(metrics.prompt_cache_hit_tokens)
        * profile.pricing.cache_hit_cny_per_million
        + Decimal(metrics.prompt_cache_miss_tokens)
        * profile.pricing.cache_miss_cny_per_million
        + Decimal(metrics.completion_tokens)
        * profile.pricing.output_cny_per_million
    ) / million


def evaluate_required_facts(answer: str, required_facts: list[str]) -> bool:
    normalized = answer.casefold()
    return all(fact.casefold() in normalized for fact in required_facts)


def write_local_report(
    report: LiveEvalReport,
    repopilot_root: Path,
) -> tuple[Path, str]:
    report_dir = repopilot_root / "live-eval"
    report_dir.mkdir(parents=True, exist_ok=True)
    file_name = report.completed_at.replace(":", "").replace("-", "")
    file_name = file_name.replace("T", "-").replace("Z", "")
    report_path = report_dir / f"{file_name}.json"
    payload = _report_payload(report)
    encoded = (
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    with report_path.open("xb") as handle:
        handle.write(encoded)
    return report_path, hashlib.sha256(encoded).hexdigest()


def build_attestation(
    report: LiveEvalReport,
    *,
    local_report_sha256: str,
) -> dict[str, object]:
    if report.status != "pass":
        raise ValueError("PASS report required")
    normalized_digest = _validate_sha256(local_report_sha256)
    _validate_utc_timestamp(report.started_at)
    _validate_utc_timestamp(report.completed_at)
    aggregate = _aggregate_metrics(report.cases)
    return {
        "schema_version": "1",
        "status": "pass",
        "tested_commit": report.tested_commit,
        "started_at": report.started_at,
        "completed_at": report.completed_at,
        "profile": {
            "id": report.profile.profile_id,
            "version": report.profile.version,
            "model": report.profile.model,
            "pricing_effective_date": report.profile.pricing.effective_date,
        },
        "rubric_version": report.rubric_version,
        "call_count": report.call_count,
        "quality_baseline": {
            "passed": report.quality_passed,
            "total": report.quality_total,
        },
        "aggregate": aggregate,
        "local_report_sha256": normalized_digest,
    }


def write_attestation(
    report: LiveEvalReport,
    *,
    local_report_sha256: str,
    docs_root: Path,
) -> Path:
    attestation = build_attestation(
        report,
        local_report_sha256=local_report_sha256,
    )
    docs_root.mkdir(parents=True, exist_ok=True)
    file_name = report.completed_at.replace(":", "").replace("-", "")
    file_name = file_name.replace("T", "-").replace("Z", "")
    path = docs_root / f"{file_name}.json"
    with path.open("x", encoding="utf-8") as handle:
        handle.write(
            json.dumps(
                attestation,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )
    return path


def conformance_failures_for_record(cases: list[CaseResult]) -> list[str]:
    failures = {
        failure
        for case in cases
        for failure in case.hard_gate_failures
    }
    if not failures:
        raise ValueError("at least one conformance failure required")
    unknown = failures - CONFORMANCE_FAILURE_GATES - INTEGRITY_FAILURE_GATES
    if unknown:
        raise ValueError("unknown failure gate")
    if failures & INTEGRITY_FAILURE_GATES:
        raise EvaluationIntegrityError("evaluation integrity failure")
    return sorted(failures)


def build_evaluated_failure_record(
    report: LiveEvalReport,
    *,
    local_report_sha256: str,
) -> dict[str, object]:
    if report.status != "fail":
        raise ValueError("FAIL report required")
    normalized_digest = _validate_sha256(local_report_sha256)
    _validate_utc_timestamp(report.completed_at)
    case_ids = [case.case_id for case in report.cases]
    if (
        report.call_count != EXPECTED_LIVE_CALLS
        or len(case_ids) != len(EXPECTED_LIVE_CASE_IDS)
        or set(case_ids) != EXPECTED_LIVE_CASE_IDS
    ):
        raise EvaluationIntegrityError("incomplete live evaluation")
    required_cases = [
        case
        for case in report.cases
        if case.case_id in REQUIRED_PROVIDER_CASE_IDS
    ]
    if len(required_cases) != len(REQUIRED_PROVIDER_CASE_IDS) or any(
        not has_evaluable_provider_contact(case.metrics)
        for case in required_cases
    ):
        raise EvaluationIntegrityError("provider contact incomplete")
    return {
        "schema_version": "1",
        "record_type": "evaluated_failure",
        "evaluation_status": "complete",
        "conformance_status": "fail",
        "evaluator_commit": report.tested_commit,
        "evaluated_at": report.completed_at,
        "profile": {
            "provider": report.profile.provider,
            "model": report.profile.model,
        },
        "rubric_version": report.rubric_version,
        "failed_gates": conformance_failures_for_record(report.cases),
        "local_report_sha256": normalized_digest,
    }


def write_evaluated_failure_record(
    report: LiveEvalReport,
    *,
    local_report_sha256: str,
    docs_root: Path,
) -> Path:
    payload = build_evaluated_failure_record(
        report,
        local_report_sha256=local_report_sha256,
    )
    failure_root = docs_root / "failures"
    failure_root.mkdir(parents=True, exist_ok=True)
    file_name = report.completed_at.replace(":", "").replace("-", "")
    file_name = file_name.replace("T", "-").replace("Z", "")
    path = failure_root / f"{file_name}.json"
    with path.open("x", encoding="utf-8") as handle:
        handle.write(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
            + "\n"
        )
    return path


def serialize_case_result(case: CaseResult) -> dict[str, object]:
    payload = _case_payload(case)
    metrics = case.metrics
    if metrics is not None:
        payload["metrics"] = {
            "availability": metrics.availability,
            "latency_ms": metrics.latency_ms,
            "requested_model": metrics.requested_model,
            "returned_model": metrics.returned_model,
            "system_fingerprint": None,
            "finish_reason": metrics.finish_reason,
            "finish_reason_status": metrics.finish_reason_status,
            "prompt_tokens": metrics.prompt_tokens,
            "prompt_cache_hit_tokens": metrics.prompt_cache_hit_tokens,
            "prompt_cache_miss_tokens": metrics.prompt_cache_miss_tokens,
            "completion_tokens": metrics.completion_tokens,
            "reasoning_tokens": metrics.reasoning_tokens,
            "total_tokens": metrics.total_tokens,
        }
    return payload


def deserialize_case_result(payload: Mapping[str, object]) -> CaseResult:
    raw_metrics = payload.get("metrics")
    metrics = (
        ProviderCallMetrics(**raw_metrics)
        if isinstance(raw_metrics, dict)
        else None
    )
    raw_cost = payload.get("cost_cny")
    raw_diagnostics = payload.get("diagnostics")
    return CaseResult(
        case_id=str(payload["case_id"]),
        status=str(payload["status"]),
        hard_gate_failures=[
            str(value)
            for value in payload.get("hard_gate_failures", [])
        ],
        quality_passed=(
            bool(payload["quality_passed"])
            if payload.get("quality_passed") is not None
            else None
        ),
        metrics=metrics,
        cost_cny=Decimal(str(raw_cost)) if raw_cost is not None else None,
        diagnostics=(
            {
                str(key): str(value)
                for key, value in raw_diagnostics.items()
            }
            if isinstance(raw_diagnostics, dict)
            else None
        ),
    )


def _report_payload(report: LiveEvalReport) -> dict[str, object]:
    return {
        "schema_version": "1",
        "status": report.status,
        "tested_commit": report.tested_commit,
        "started_at": report.started_at,
        "completed_at": report.completed_at,
        "profile": {
            "id": report.profile.profile_id,
            "version": report.profile.version,
            "provider": report.profile.provider,
            "model": report.profile.model,
            "pricing_effective_date": report.profile.pricing.effective_date,
        },
        "rubric_version": report.rubric_version,
        "call_count": report.call_count,
        "quality_baseline": {
            "passed": report.quality_passed,
            "total": report.quality_total,
        },
        "cases": [_case_payload(case) for case in report.cases],
        "aggregate": _aggregate_metrics(report.cases),
    }


def _case_payload(case: CaseResult) -> dict[str, object]:
    return {
        "case_id": case.case_id,
        "status": case.status,
        "hard_gate_failures": list(case.hard_gate_failures),
        "quality_passed": case.quality_passed,
        "metrics": _metrics_payload(case.metrics),
        "cost_cny": str(case.cost_cny) if case.cost_cny is not None else None,
        "diagnostics": dict(case.diagnostics) if case.diagnostics else None,
    }


def _metrics_payload(metrics: ProviderCallMetrics | None) -> dict[str, object] | None:
    if metrics is None:
        return None
    return {
        "availability": metrics.availability,
        "latency_ms": metrics.latency_ms,
        "requested_model": metrics.requested_model,
        "returned_model": metrics.returned_model,
        "system_fingerprint_status": (
            "available" if metrics.system_fingerprint else "unavailable"
        ),
        "finish_reason": metrics.finish_reason,
        "finish_reason_status": metrics.finish_reason_status,
        "prompt_tokens": metrics.prompt_tokens,
        "prompt_cache_hit_tokens": metrics.prompt_cache_hit_tokens,
        "prompt_cache_miss_tokens": metrics.prompt_cache_miss_tokens,
        "completion_tokens": metrics.completion_tokens,
        "reasoning_tokens": metrics.reasoning_tokens,
        "total_tokens": metrics.total_tokens,
    }


def _aggregate_metrics(cases: list[CaseResult]) -> dict[str, object]:
    metrics = [case.metrics for case in cases if case.metrics is not None]
    costs = [case.cost_cny for case in cases if case.cost_cny is not None]

    def sum_optional(name: str) -> int:
        return sum(
            int(value)
            for item in metrics
            if (value := getattr(item, name)) is not None
        )

    return {
        "latency_ms": sum(item.latency_ms for item in metrics),
        "prompt_tokens": sum_optional("prompt_tokens"),
        "prompt_cache_hit_tokens": sum_optional("prompt_cache_hit_tokens"),
        "prompt_cache_miss_tokens": sum_optional("prompt_cache_miss_tokens"),
        "completion_tokens": sum_optional("completion_tokens"),
        "reasoning_tokens": sum_optional("reasoning_tokens"),
        "total_tokens": sum_optional("total_tokens"),
        "cost_cny": str(sum(costs, Decimal("0"))),
    }


def _status_class_for_error(error_class: str) -> str:
    normalized = error_class.casefold()
    if "timeout" in normalized:
        return "timeout"
    if "connect" in normalized or "network" in normalized:
        return "network_error"
    if "httpstatus" in normalized:
        return "http_error"
    if "json" in normalized or "valueerror" in normalized:
        return "parse_error"
    if "validation" in normalized or "finishreason" in normalized:
        return "validation_error"
    return "provider_error"


def _diagnostic_code(value: str) -> str:
    if not value:
        return ""
    candidate = value.split(":", 1)[0].split()[0]
    if candidate.casefold() in {"http", "https"}:
        return "ProviderError"
    if not candidate or len(candidate) > 80:
        return "ProviderError"
    allowed = set("._-")
    if not all(character.isalnum() or character in allowed for character in candidate):
        return "ProviderError"
    if not any(character.isalpha() for character in candidate):
        return "ProviderError"
    return candidate


def _phase_for_status_class(status_class: str) -> str:
    if status_class in {"network_error", "timeout"}:
        return "provider_http_request"
    if status_class == "http_error":
        return "provider_http_status"
    if status_class == "parse_error":
        return "provider_response_parse"
    return "provider_response_validation"


def _validate_sha256(value: str) -> str:
    normalized = value.casefold()
    if len(normalized) != 64 or any(
        character not in "0123456789abcdef"
        for character in normalized
    ):
        raise ValueError("valid report SHA-256 required")
    return normalized


def _validate_utc_timestamp(value: str) -> None:
    if not value.endswith("Z"):
        raise ValueError("UTC completion time required")
    try:
        datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise ValueError("UTC completion time required") from exc
