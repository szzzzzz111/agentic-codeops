from dataclasses import dataclass, field
import os
from typing import Protocol

import httpx


@dataclass(frozen=True)
class ModelProviderRequest:
    original_query: str
    question_type: str
    evidence: list[dict[str, str | int]]


@dataclass(frozen=True)
class ModelProviderResponse:
    answer: str
    audit_summary: dict[str, str] = field(default_factory=dict)


class ModelProvider(Protocol):
    def generate(self, request: ModelProviderRequest) -> ModelProviderResponse:
        """Generate an answer from already-budgeted evidence."""


class FakeModelProvider:
    provider_name = "fake"
    model_name = "deterministic-fake"

    def generate(self, request: ModelProviderRequest) -> ModelProviderResponse:
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
        client: httpx.Client | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.client = client or httpx.Client(timeout=timeout_seconds)

    def generate(self, request: ModelProviderRequest) -> ModelProviderResponse:
        try:
            response = self.client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "你只能基于给定仓库证据回答，并必须引用证据 citation。"
                            ),
                        },
                        {
                            "role": "user",
                            "content": _format_provider_prompt(request),
                        },
                    ],
                    "temperature": 0,
                },
            )
            response.raise_for_status()
            data = response.json()
            answer = data["choices"][0]["message"]["content"]
        except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as exc:
            return ModelProviderResponse(
                answer="",
                audit_summary={
                    "provider": self.provider_name,
                    "model": self.model,
                    "status": "error",
                    "error_class": type(exc).__name__,
                },
            )

        return ModelProviderResponse(
            answer=str(answer),
            audit_summary={
                "provider": self.provider_name,
                "model": self.model,
                "status": "success",
            },
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
        if not base_url or not api_key or not model:
            return _ConfigErrorProvider(model=model)
        return OpenAICompatibleModelProvider(
            base_url=base_url,
            api_key=api_key,
            model=model,
            timeout_seconds=timeout,
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
