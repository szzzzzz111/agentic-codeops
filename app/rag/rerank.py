import re
from dataclasses import dataclass
from typing import Protocol

from app.rag.query_understanding import SearchPlan
from app.rag.repo_rag import RetrievalResult

CitationKey = tuple[str, int, int]


@dataclass(frozen=True)
class RepoRerankResult:
    results: list[RetrievalResult]
    provider_name: str = "deterministic"
    input_count: int = 0
    fallback_reason: str | None = None

    def audit_summary(self) -> dict[str, str | int]:
        summary: dict[str, str | int] = {
            "rerank_provider": self.provider_name,
            "rerank_status": "fallback" if self.fallback_reason else "success",
            "rerank_input_count": self.input_count,
            "rerank_output_count": len(self.results),
        }
        if self.fallback_reason:
            summary["rerank_fallback_reason"] = self.fallback_reason
        return summary


class RepoReranker(Protocol):
    provider_name: str

    def rerank(
        self,
        results: list[RetrievalResult],
        *,
        plan: SearchPlan,
        original_result_keys: set[CitationKey],
        max_results: int,
    ) -> RepoRerankResult:
        ...


class DeterministicRepoReranker:
    provider_name = "deterministic"

    def rerank(
        self,
        results: list[RetrievalResult],
        *,
        plan: SearchPlan,
        original_result_keys: set[CitationKey],
        max_results: int,
    ) -> RepoRerankResult:
        ranked = sorted(
            results,
            key=lambda result: (
                -_rerank_score(result, plan, original_result_keys),
                result.citation.file_path,
                result.citation.start_line,
            ),
        )
        return RepoRerankResult(
            results=ranked[:max_results],
            provider_name=self.provider_name,
            input_count=len(results),
        )


def rerank_with_fallback(
    results: list[RetrievalResult],
    *,
    plan: SearchPlan,
    original_result_keys: set[CitationKey],
    max_results: int,
    reranker: RepoReranker,
) -> RepoRerankResult:
    try:
        return reranker.rerank(
            results,
            plan=plan,
            original_result_keys=original_result_keys,
            max_results=max_results,
        )
    except Exception as exc:  # noqa: BLE001 - Provider boundary intentionally falls back.
        return RepoRerankResult(
            results=results[:max_results],
            provider_name=getattr(reranker, "provider_name", "unknown"),
            input_count=len(results),
            fallback_reason=type(exc).__name__,
        )


def _rerank_score(
    result: RetrievalResult,
    plan: SearchPlan,
    original_result_keys: set[CitationKey],
) -> int:
    score = result.score
    key = (
        result.citation.file_path,
        result.citation.start_line,
        result.citation.end_line,
    )
    if key in original_result_keys:
        score += 10000
    if result.citation.file_path in plan.path_hints:
        score += 1000
    lower_path = result.citation.file_path.lower()
    lower_text = result.chunk.text.lower()
    for path_hint in plan.path_hints:
        if path_hint.lower() in lower_path:
            score += 500
    for symbol in plan.symbols:
        if _contains_exact_token(result.chunk.text, symbol):
            score += 300
        elif symbol.lower() in lower_text or symbol.lower() in lower_path:
            score += 100
    for keyword in plan.keywords:
        if _contains_exact_token(result.chunk.text, keyword):
            score += 40
        elif keyword.lower() in lower_text or keyword.lower() in lower_path:
            score += 20
    return score


def _contains_exact_token(text: str, token: str) -> bool:
    return re.search(rf"(?<![A-Za-z0-9_]){re.escape(token)}(?![A-Za-z0-9_])", text) is not None
