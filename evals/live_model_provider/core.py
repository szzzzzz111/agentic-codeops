from __future__ import annotations

from dataclasses import dataclass, field
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
REQUIRED_ENV_NAMES = (
    "REPOPILOT_MODEL_PROVIDER",
    "REPOPILOT_MODEL_BASE_URL",
    "REPOPILOT_MODEL_API_KEY",
    "REPOPILOT_MODEL_NAME",
    "REPOPILOT_MODEL_THINKING",
)


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
    report_path.write_bytes(encoded)
    return report_path, hashlib.sha256(encoded).hexdigest()


def build_attestation(
    report: LiveEvalReport,
    *,
    local_report_sha256: str,
) -> dict[str, object]:
    if report.status != "pass":
        raise ValueError("PASS report required")
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
        "local_report_sha256": local_report_sha256,
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
    path.write_text(
        json.dumps(attestation, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
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
