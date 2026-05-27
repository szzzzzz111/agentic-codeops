from dataclasses import dataclass, field
import re
from typing import Protocol

from app.rag.query_understanding import QueryUnderstanding, SearchPlan


ORIGINAL_VARIANT_ID = "original"
CODE_EVIDENCE_VARIANT_IDS = ("definition", "usage", "configuration", "tests")
MAX_ADDITIONAL_VARIANTS = 3


@dataclass(frozen=True)
class QueryVariant:
    variant_id: str
    query_text: str
    question_type: str
    keywords: list[str] = field(default_factory=list)
    symbols: list[str] = field(default_factory=list)
    path_hints: list[str] = field(default_factory=list)
    max_results: int = 8
    retrieval_mode: str = "hybrid"
    weight: float = 1.0

    def terms(self) -> list[str]:
        return _unique([*self.path_hints, *self.symbols, *self.keywords])

    def to_search_plan(self) -> SearchPlan:
        return SearchPlan(
            original_query=self.query_text,
            question_type=self.question_type,
            keywords=self.keywords,
            symbols=self.symbols,
            path_hints=self.path_hints,
            max_results=self.max_results,
            retrieval_mode=self.retrieval_mode,
        )


@dataclass(frozen=True)
class QueryRewriteResult:
    original_plan: SearchPlan
    variants: list[QueryVariant]
    provider_name: str = "deterministic"
    fallback_reason: str | None = None

    def audit_summary(self) -> dict[str, str | int]:
        summary: dict[str, str | int] = {
            "rewrite_provider": self.provider_name,
            "rewrite_status": "fallback" if self.fallback_reason else "success",
            "variant_count": len(self.variants),
        }
        if self.fallback_reason:
            summary["rewrite_fallback_reason"] = self.fallback_reason
        return summary


class QueryRewriteProvider(Protocol):
    provider_name: str

    def rewrite(self, plan: SearchPlan) -> QueryRewriteResult:
        ...


class DeterministicQueryRewriteProvider:
    provider_name = "deterministic"

    def __init__(
        self,
        *,
        query_understanding: QueryUnderstanding | None = None,
    ) -> None:
        self.query_understanding = query_understanding or QueryUnderstanding()

    def rewrite(self, plan: SearchPlan) -> QueryRewriteResult:
        original = _variant_from_plan(ORIGINAL_VARIANT_ID, plan, plan.original_query)
        if not plan.terms():
            return QueryRewriteResult(
                original_plan=plan,
                variants=[original],
                provider_name=self.provider_name,
                fallback_reason="no_search_terms",
            )

        variants = [original]
        seen = {_variant_key(original)}
        for variant_id in CODE_EVIDENCE_VARIANT_IDS:
            variant = self._build_code_evidence_variant(variant_id, plan)
            key = _variant_key(variant)
            if key in seen:
                continue
            variants.append(variant)
            seen.add(key)
            if len(variants) >= MAX_ADDITIONAL_VARIANTS + 1:
                break

        return QueryRewriteResult(
            original_plan=plan,
            variants=variants,
            provider_name=self.provider_name,
        )

    def _build_code_evidence_variant(
        self,
        variant_id: str,
        plan: SearchPlan,
    ) -> QueryVariant:
        terms = " ".join(plan.terms()) or plan.original_query
        prefix = {
            "definition": "definition class function interface",
            "usage": "usage call caller callee",
            "configuration": "configuration config env provider factory",
            "tests": "tests pytest validation fallback",
        }[variant_id]
        query_text = f"{prefix} {terms}".strip()
        variant_plan = self.query_understanding.build_search_plan(query_text)
        return QueryVariant(
            variant_id=variant_id,
            query_text=query_text,
            question_type=plan.question_type,
            keywords=variant_plan.keywords,
            symbols=variant_plan.symbols,
            path_hints=variant_plan.path_hints,
            max_results=plan.max_results,
            retrieval_mode=plan.retrieval_mode,
            weight=0.75,
        )


def build_original_rewrite_result(
    plan: SearchPlan,
    *,
    provider: QueryRewriteProvider,
) -> QueryRewriteResult:
    try:
        return provider.rewrite(plan)
    except Exception as exc:
        return QueryRewriteResult(
            original_plan=plan,
            variants=[_variant_from_plan(ORIGINAL_VARIANT_ID, plan, plan.original_query)],
            provider_name=getattr(provider, "provider_name", "unknown"),
            fallback_reason=type(exc).__name__,
        )


def _variant_from_plan(
    variant_id: str,
    plan: SearchPlan,
    query_text: str,
) -> QueryVariant:
    return QueryVariant(
        variant_id=variant_id,
        query_text=query_text,
        question_type=plan.question_type,
        keywords=plan.keywords,
        symbols=plan.symbols,
        path_hints=plan.path_hints,
        max_results=plan.max_results,
        retrieval_mode=plan.retrieval_mode,
    )


def _variant_key(
    variant: QueryVariant,
) -> tuple[str, tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    return (
        _normalize(variant.query_text),
        _normalized_terms(variant.keywords),
        _normalized_terms(variant.symbols),
        _normalized_terms(variant.path_hints),
    )


def _normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def _normalized_terms(values: list[str]) -> tuple[str, ...]:
    return tuple(_normalize(value) for value in values)


def _unique(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        if not value or value in seen:
            continue
        result.append(value)
        seen.add(value)
    return result
