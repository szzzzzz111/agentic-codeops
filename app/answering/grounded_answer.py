from dataclasses import dataclass, field
from pathlib import PurePosixPath, PureWindowsPath
import re

from app.providers.model_provider import (
    ModelProvider,
    ModelProviderRequest,
    ModelProviderResponse,
)
from app.rag.evidence import EvidencePack


FALLBACK_NO_EVIDENCE = "无法基于仓库证据回答该问题。"
FALLBACK_PROVIDER = "无法基于当前仓库证据生成可靠回答。"
_CITATION_PATTERN = re.compile(
    r"(?<![A-Za-z0-9_./:-])([A-Za-z0-9_./-]+\.[A-Za-z0-9_]+):(\d+)-(\d+)"
)
_BROAD_CITATION_PATTERN = re.compile(r"\S+:\d+-\d+")
_ALLOWED_AUDIT_KEYS = {
    "provider",
    "model",
    "status",
    "error_class",
    "fallback_reason",
    "latency_ms",
}


@dataclass(frozen=True)
class CitationValidationResult:
    valid: bool
    citations: list[str] = field(default_factory=list)
    reason: str = ""


@dataclass(frozen=True)
class GroundedAnswerResult:
    answer: str
    audit_summary: dict[str, str] = field(default_factory=dict)


class GroundedAnswerGenerator:
    def __init__(self, provider: ModelProvider) -> None:
        self.provider = provider

    def generate(self, evidence_pack: EvidencePack) -> GroundedAnswerResult:
        evidence = _included_evidence(evidence_pack)
        if not evidence:
            return GroundedAnswerResult(
                answer=FALLBACK_NO_EVIDENCE,
                audit_summary={
                    "provider": "none",
                    "model": "none",
                    "status": "fallback",
                    "fallback_reason": "no_evidence",
                },
            )

        provider_response = self.provider.generate(
            ModelProviderRequest(
                original_query=evidence_pack.original_query,
                question_type=evidence_pack.question_type,
                evidence=evidence,
            )
        )
        if provider_response.audit_summary.get("status") != "success":
            return _fallback(provider_response, "provider_error")

        validation = validate_answer_citations(provider_response.answer, evidence_pack)
        if not validation.valid:
            return _fallback(provider_response, validation.reason)

        return GroundedAnswerResult(
            answer=provider_response.answer,
            audit_summary=_sanitize_audit_summary(provider_response.audit_summary),
        )


def validate_answer_citations(
    answer: str,
    evidence_pack: EvidencePack,
) -> CitationValidationResult:
    allowed = {
        f"{item.file_path}:{item.start_line}-{item.end_line}"
        for item in evidence_pack.items
        if item.included
    }
    citations: list[str] = []
    invalid_seen = False

    for match in _CITATION_PATTERN.finditer(answer):
        path = match.group(1)
        citation = f"{path}:{match.group(2)}-{match.group(3)}"
        if _is_absolute_path(path) or citation not in allowed:
            invalid_seen = True
            continue
        citations.append(citation)

    broad_matches = {match.group(0).rstrip("。，,.；;)）]】") for match in _BROAD_CITATION_PATTERN.finditer(answer)}
    if broad_matches - set(citations):
        invalid_seen = True

    if invalid_seen:
        return CitationValidationResult(
            valid=False,
            citations=citations,
            reason="invalid_citation",
        )
    if not citations:
        return CitationValidationResult(
            valid=False,
            citations=[],
            reason="missing_citation",
        )
    return CitationValidationResult(valid=True, citations=citations)


def _fallback(
    provider_response: ModelProviderResponse,
    reason: str,
) -> GroundedAnswerResult:
    return GroundedAnswerResult(
        answer=FALLBACK_PROVIDER,
        audit_summary={
            **_sanitize_audit_summary(provider_response.audit_summary),
            "status": "fallback",
            "fallback_reason": reason,
        },
    )


def _sanitize_audit_summary(audit_summary: dict[str, str]) -> dict[str, str]:
    sanitized = {
        key: value
        for key, value in audit_summary.items()
        if key in _ALLOWED_AUDIT_KEYS
    }
    if sanitized.get("status") == "success":
        sanitized.pop("fallback_reason", None)
    return sanitized


def _included_evidence(evidence_pack: EvidencePack) -> list[dict[str, str | int]]:
    return [
        {
            "file_path": item.file_path,
            "start_line": item.start_line,
            "end_line": item.end_line,
            "snippet": item.snippet,
        }
        for item in evidence_pack.items
        if item.included and item.snippet
    ]


def _is_absolute_path(file_path: str) -> bool:
    return PureWindowsPath(file_path).is_absolute() or PurePosixPath(
        file_path
    ).is_absolute()
