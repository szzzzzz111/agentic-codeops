import json
from dataclasses import dataclass, field
from typing import Protocol

from app.providers.model_provider import (
    ModelProvider,
    ModelProviderRequest,
    StructuredOutputInstruction,
)

_PATCH_OUTPUT_INSTRUCTION = StructuredOutputInstruction(
    name="patch_proposal",
    json_example=(
        '{"summary":"...","target_files":["relative/path.py"],'
        '"diff":"--- a/relative/path.py\\n+++ b/relative/path.py\\n",'
        '"citations":["relative/path.py:1-2"]}'
    ),
    max_output_tokens=8000,
)


@dataclass(frozen=True)
class PatchAuthoringProviderRequest:
    original_query: str
    question_type: str
    evidence: list[dict[str, str | int]]


@dataclass(frozen=True)
class PatchAuthoringProviderResponse:
    summary: str = ""
    target_files: list[str] = field(default_factory=list)
    diff_text: str = ""
    citations: list[str] = field(default_factory=list)
    audit_summary: dict[str, str] = field(default_factory=dict)


class PatchAuthoringProvider(Protocol):
    def generate_patch(
        self,
        request: PatchAuthoringProviderRequest,
    ) -> PatchAuthoringProviderResponse:
        """Generate a structured patch proposal from already-budgeted evidence."""


class FakePatchAuthoringProvider:
    provider_name = "fake"

    def generate_patch(
        self,
        request: PatchAuthoringProviderRequest,
    ) -> PatchAuthoringProviderResponse:
        return PatchAuthoringProviderResponse(
            audit_summary={
                "provider": self.provider_name,
                "status": "fallback",
                "fallback_reason": "fake_provider_no_diff",
            }
        )


class ModelPatchAuthoringProvider:
    def __init__(self, provider: ModelProvider) -> None:
        self.provider = provider

    def generate_patch(
        self,
        request: PatchAuthoringProviderRequest,
    ) -> PatchAuthoringProviderResponse:
        provider_response = self.provider.generate(
            ModelProviderRequest(
                original_query=request.original_query,
                question_type=request.question_type,
                evidence=request.evidence,
                output_mode="json_object",
                structured_output=_PATCH_OUTPUT_INSTRUCTION,
            )
        )
        audit = dict(provider_response.audit_summary)
        if audit.get("status") != "success":
            return PatchAuthoringProviderResponse(audit_summary=audit)
        try:
            data = json.loads(provider_response.answer)
            summary = str(data["summary"]).strip()
            target_files = [str(item).strip() for item in data["target_files"]]
            diff_text = str(data["diff"]).strip()
            citations = [str(item).strip() for item in data["citations"]]
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            return PatchAuthoringProviderResponse(
                audit_summary={
                    **audit,
                    "status": "error",
                    "error_class": type(exc).__name__,
                }
            )
        return PatchAuthoringProviderResponse(
            summary=summary,
            target_files=target_files,
            diff_text=diff_text + "\n",
            citations=citations,
            audit_summary=audit,
        )
