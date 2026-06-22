from dataclasses import dataclass, field
import json
import os
import re
from time import perf_counter
from typing import Protocol

import httpx


OUTPUT_MODE_GROUNDED_TEXT = "grounded_text"
OUTPUT_MODE_JSON_OBJECT = "json_object"
MAX_STRUCTURED_OUTPUT_TOKENS = 16384
MAX_STRUCTURED_OUTPUT_EXAMPLE_CHARS = 4096
STRUCTURED_OUTPUT_NAME_PATTERN = re.compile(r"[A-Za-z][A-Za-z0-9_.-]{0,63}")


@dataclass(frozen=True)
class StructuredOutputInstruction:
    name: str
    json_example: str
    max_output_tokens: int


@dataclass(frozen=True)
class ModelProviderRequest:
    original_query: str
    question_type: str
    evidence: list[dict[str, str | int]]
    output_mode: str = OUTPUT_MODE_GROUNDED_TEXT
    structured_output: StructuredOutputInstruction | None = None


@dataclass(frozen=True)
class ProviderCallMetrics:
    availability: str
    latency_ms: int
    requested_model: str
    returned_model: str | None = None
    system_fingerprint: str | None = None
    finish_reason: str | None = None
    finish_reason_status: str = "unavailable"
    prompt_tokens: int | None = None
    prompt_cache_hit_tokens: int | None = None
    prompt_cache_miss_tokens: int | None = None
    completion_tokens: int | None = None
    reasoning_tokens: int | None = None
    total_tokens: int | None = None


@dataclass(frozen=True)
class ModelProviderResponse:
    answer: str
    audit_summary: dict[str, str] = field(default_factory=dict)
    metrics: ProviderCallMetrics | None = None


class ModelProvider(Protocol):
    def generate(self, request: ModelProviderRequest) -> ModelProviderResponse:
        """Generate an answer from already-budgeted evidence."""


class FakeModelProvider:
    provider_name = "fake"
    model_name = "deterministic-fake"

    def generate(self, request: ModelProviderRequest) -> ModelProviderResponse:
        validation_error = _validate_request(request)
        if validation_error:
            return _error_response(
                provider=self.provider_name,
                model=self.model_name,
                error_class=validation_error,
            )
        if request.output_mode == OUTPUT_MODE_JSON_OBJECT:
            return _error_response(
                provider=self.provider_name,
                model=self.model_name,
                error_class="UnsupportedOutputModeError",
            )
        if not request.evidence:
            answer = ""
        else:
            first = request.evidence[0]
            answer = (
                f"基于仓库证据，问题 `{request.original_query}` 的相关实现位于 "
                f"{first['file_path']}:{first['start_line']}-{first['end_line']}。"
            )
        return ModelProviderResponse(
            answer=answer,
            audit_summary={
                "provider": self.provider_name,
                "model": self.model_name,
                "status": "success",
            },
        )


class OpenAICompatibleModelProvider:
    provider_name = "openai_compatible"

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        timeout_seconds: float = 30.0,
        thinking_mode: str | None = None,
        client: httpx.Client | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.thinking_mode = thinking_mode
        self.client = client or httpx.Client(timeout=timeout_seconds)

    def generate(self, request: ModelProviderRequest) -> ModelProviderResponse:
        if self.thinking_mode not in (None, "disabled"):
            return _error_response(
                provider=self.provider_name,
                model=self.model,
                error_class="ProviderConfigError",
            )
        validation_error = _validate_request(request)
        if validation_error:
            return _error_response(
                provider=self.provider_name,
                model=self.model,
                error_class=validation_error,
            )
        started_at = perf_counter()
        try:
            response = self.client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=_request_payload(
                    request,
                    model=self.model,
                    thinking_mode=self.thinking_mode,
                ),
            )
            response.raise_for_status()
            data = response.json()
            choice = data["choices"][0]
            answer = choice["message"]["content"]
        except (
            httpx.HTTPError,
            KeyError,
            IndexError,
            TypeError,
            ValueError,
            RecursionError,
        ) as exc:
            return ModelProviderResponse(
                answer="",
                audit_summary={
                    "provider": self.provider_name,
                    "model": self.model,
                    "status": "error",
                    "error_class": type(exc).__name__,
                },
                metrics=_unavailable_metrics(
                    requested_model=self.model,
                    started_at=started_at,
                ),
            )

        metrics = _build_metrics(
            data=data,
            choice=choice,
            requested_model=self.model,
            started_at=started_at,
        )
        if metrics.finish_reason_status == "incomplete":
            return _error_response(
                provider=self.provider_name,
                model=self.model,
                error_class="ProviderFinishReasonError",
                metrics=metrics,
            )
        if not isinstance(answer, str) or not answer.strip():
            return _error_response(
                provider=self.provider_name,
                model=self.model,
                error_class="ProviderResponseValidationError",
                metrics=metrics,
            )
        if request.output_mode == OUTPUT_MODE_JSON_OBJECT:
            try:
                parsed = json.loads(answer)
            except (TypeError, ValueError, json.JSONDecodeError, RecursionError):
                return _error_response(
                    provider=self.provider_name,
                    model=self.model,
                    error_class="ProviderResponseValidationError",
                    metrics=metrics,
                )
            if not isinstance(parsed, dict):
                return _error_response(
                    provider=self.provider_name,
                    model=self.model,
                    error_class="ProviderResponseValidationError",
                    metrics=metrics,
                )

        return ModelProviderResponse(
            answer=answer,
            audit_summary={
                "provider": self.provider_name,
                "model": self.model,
                "status": "success",
            },
            metrics=metrics,
        )


class _ConfigErrorProvider:
    provider_name = "openai_compatible"

    def __init__(self, model: str = "") -> None:
        self.model = model

    def generate(self, request: ModelProviderRequest) -> ModelProviderResponse:
        return ModelProviderResponse(
            answer="",
            audit_summary={
                "provider": self.provider_name,
                "model": self.model,
                "status": "error",
                "error_class": "ProviderConfigError",
            },
        )


def load_model_provider_from_env() -> ModelProvider:
    provider = os.getenv("REPOPILOT_MODEL_PROVIDER", "fake").strip().lower()
    if provider in ("", "fake"):
        return FakeModelProvider()
    if provider == "openai_compatible":
        base_url = os.getenv("REPOPILOT_MODEL_BASE_URL", "").strip()
        api_key = os.getenv("REPOPILOT_MODEL_API_KEY", "").strip()
        model = os.getenv("REPOPILOT_MODEL_NAME", "").strip()
        timeout = _coerce_timeout(os.getenv("REPOPILOT_MODEL_TIMEOUT_SECONDS"))
        thinking_mode = os.getenv("REPOPILOT_MODEL_THINKING", "").strip() or None
        if not base_url or not api_key or not model:
            return _ConfigErrorProvider(model=model)
        if thinking_mode not in (None, "disabled"):
            return _ConfigErrorProvider(model=model)
        return OpenAICompatibleModelProvider(
            base_url=base_url,
            api_key=api_key,
            model=model,
            timeout_seconds=timeout,
            thinking_mode=thinking_mode,
        )
    return _ConfigErrorProvider(model="")


def _format_provider_prompt(request: ModelProviderRequest) -> str:
    evidence_lines = []
    for item in request.evidence:
        citation = f"{item['file_path']}:{item['start_line']}-{item['end_line']}"
        evidence_lines.append(f"[{citation}]\n{item['snippet']}")
    evidence = "\n\n".join(evidence_lines)
    return (
        f"问题类型：{request.question_type}\n"
        f"用户问题：{request.original_query}\n"
        f"仓库证据：\n{evidence}"
    )


def _coerce_timeout(raw: str | None) -> float:
    if not raw:
        return 30.0
    try:
        timeout = float(raw)
    except ValueError:
        return 30.0
    return max(timeout, 0.1)


def _validate_request(request: ModelProviderRequest) -> str:
    if request.output_mode not in {
        OUTPUT_MODE_GROUNDED_TEXT,
        OUTPUT_MODE_JSON_OBJECT,
    }:
        return "ProviderRequestValidationError"
    instruction = request.structured_output
    if request.output_mode == OUTPUT_MODE_GROUNDED_TEXT:
        if instruction is not None:
            return "ProviderRequestValidationError"
        return ""
    if not isinstance(instruction, StructuredOutputInstruction):
        return "ProviderRequestValidationError"
    if (
        not isinstance(instruction.name, str)
        or STRUCTURED_OUTPUT_NAME_PATTERN.fullmatch(instruction.name) is None
        or not isinstance(instruction.json_example, str)
        or not instruction.json_example.strip()
        or len(instruction.json_example) > MAX_STRUCTURED_OUTPUT_EXAMPLE_CHARS
    ):
        return "ProviderRequestValidationError"
    try:
        example = json.loads(instruction.json_example)
    except (TypeError, ValueError, json.JSONDecodeError, RecursionError):
        return "ProviderRequestValidationError"
    if not isinstance(example, dict):
        return "ProviderRequestValidationError"
    if (
        type(instruction.max_output_tokens) is not int
        or not 1 <= instruction.max_output_tokens <= MAX_STRUCTURED_OUTPUT_TOKENS
    ):
        return "ProviderRequestValidationError"
    return ""


def _error_response(
    *,
    provider: str,
    model: str,
    error_class: str,
    metrics: ProviderCallMetrics | None = None,
) -> ModelProviderResponse:
    return ModelProviderResponse(
        answer="",
        audit_summary={
            "provider": provider,
            "model": model,
            "status": "error",
            "error_class": error_class,
        },
        metrics=metrics,
    )


def _build_metrics(
    *,
    data: object,
    choice: object,
    requested_model: str,
    started_at: float,
) -> ProviderCallMetrics:
    response_data = data if isinstance(data, dict) else {}
    choice_data = choice if isinstance(choice, dict) else {}
    usage = response_data.get("usage")
    usage_data = usage if isinstance(usage, dict) else {}
    details = usage_data.get("completion_tokens_details")
    detail_data = details if isinstance(details, dict) else {}

    returned_model = _optional_str(response_data.get("model"))
    system_fingerprint = _optional_str(response_data.get("system_fingerprint"))
    finish_reason = _optional_str(choice_data.get("finish_reason"))
    prompt_tokens = _optional_int(usage_data.get("prompt_tokens"))
    cache_hit_tokens = _optional_int(usage_data.get("prompt_cache_hit_tokens"))
    cache_miss_tokens = _optional_int(usage_data.get("prompt_cache_miss_tokens"))
    completion_tokens = _optional_int(usage_data.get("completion_tokens"))
    reasoning_tokens = _optional_int(detail_data.get("reasoning_tokens"))
    total_tokens = _optional_int(usage_data.get("total_tokens"))

    core_values = (
        returned_model,
        finish_reason,
        prompt_tokens,
        completion_tokens,
        total_tokens,
    )
    if all(value is not None for value in core_values):
        availability = "available"
    elif any(
        value is not None
        for value in (
            returned_model,
            system_fingerprint,
            finish_reason,
            prompt_tokens,
            cache_hit_tokens,
            cache_miss_tokens,
            completion_tokens,
            reasoning_tokens,
            total_tokens,
        )
    ):
        availability = "partial"
    else:
        availability = "unavailable"

    return ProviderCallMetrics(
        availability=availability,
        latency_ms=_elapsed_ms(started_at),
        requested_model=requested_model,
        returned_model=returned_model,
        system_fingerprint=system_fingerprint,
        finish_reason=finish_reason,
        finish_reason_status=_finish_reason_status(finish_reason),
        prompt_tokens=prompt_tokens,
        prompt_cache_hit_tokens=cache_hit_tokens,
        prompt_cache_miss_tokens=cache_miss_tokens,
        completion_tokens=completion_tokens,
        reasoning_tokens=reasoning_tokens,
        total_tokens=total_tokens,
    )


def _unavailable_metrics(
    *,
    requested_model: str,
    started_at: float,
) -> ProviderCallMetrics:
    return ProviderCallMetrics(
        availability="unavailable",
        latency_ms=_elapsed_ms(started_at),
        requested_model=requested_model,
    )


def _elapsed_ms(started_at: float) -> int:
    return max(0, round((perf_counter() - started_at) * 1000))


def _optional_str(value: object) -> str | None:
    return value if isinstance(value, str) and value else None


def _optional_int(value: object) -> int | None:
    if type(value) is int and value >= 0:
        return value
    return None


def _finish_reason_status(finish_reason: str | None) -> str:
    if finish_reason is None:
        return "unavailable"
    if finish_reason == "stop":
        return "complete"
    if finish_reason in {
        "length",
        "content_filter",
        "tool_calls",
        "insufficient_system_resource",
    }:
        return "incomplete"
    return "unknown"


def _request_payload(
    request: ModelProviderRequest,
    *,
    model: str,
    thinking_mode: str | None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": _system_prompt(request),
            },
            {
                "role": "user",
                "content": _format_provider_prompt(request),
            },
        ],
        "temperature": 0,
    }
    if request.output_mode == OUTPUT_MODE_JSON_OBJECT:
        instruction = request.structured_output
        if instruction is None:
            raise ValueError("structured output instruction required")
        payload["response_format"] = {"type": "json_object"}
        payload["max_tokens"] = instruction.max_output_tokens
    if thinking_mode == "disabled":
        payload["thinking"] = {"type": "disabled"}
    return payload


def _system_prompt(request: ModelProviderRequest) -> str:
    if request.output_mode == OUTPUT_MODE_GROUNDED_TEXT:
        return "你只能基于给定仓库证据回答，并必须引用证据 citation。"
    instruction = request.structured_output
    if instruction is None:
        raise ValueError("structured output instruction required")
    return (
        f"Return only one JSON object for `{instruction.name}`. "
        "Do not include markdown fences or explanatory prose. "
        f"Use this example shape: {instruction.json_example}"
    )
