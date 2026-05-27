from app.rag.query_understanding import QueryUnderstanding
from app.rag.query_rewrite import (
    DeterministicQueryRewriteProvider,
    QueryVariant,
    QueryRewriteProvider,
    _variant_key,
    build_original_rewrite_result,
)


def test_deterministic_rewrite_keeps_original_and_stable_code_evidence_variants() -> None:
    plan = QueryUnderstanding().build_search_plan(
        "ModelProvider 在 app/providers/model_provider.py 里怎么接入?"
    )

    result = DeterministicQueryRewriteProvider().rewrite(plan)

    assert [variant.variant_id for variant in result.variants] == [
        "original",
        "definition",
        "usage",
        "configuration",
    ]
    assert len(result.variants) == 4
    assert result.variants[0].query_text == plan.original_query
    assert all(variant.question_type == plan.question_type for variant in result.variants)
    assert result.audit_summary() == {
        "rewrite_provider": "deterministic",
        "rewrite_status": "success",
        "variant_count": 4,
    }


def test_deterministic_rewrite_deduplicates_variants_and_falls_back_without_terms() -> None:
    empty_plan = QueryUnderstanding().build_search_plan("你好")

    result = DeterministicQueryRewriteProvider().rewrite(empty_plan)

    assert [variant.variant_id for variant in result.variants] == ["original"]
    assert result.fallback_reason == "no_search_terms"
    assert result.audit_summary()["variant_count"] == 1
    assert result.audit_summary()["rewrite_fallback_reason"] == "no_search_terms"


def test_variant_dedup_key_keeps_term_fields_separate() -> None:
    keyword_variant = QueryVariant(
        variant_id="usage",
        query_text="same query",
        question_type="implementation_explanation",
        keywords=["beta"],
        symbols=["alpha"],
    )
    path_variant = QueryVariant(
        variant_id="configuration",
        query_text="same query",
        question_type="implementation_explanation",
        keywords=["beta"],
        path_hints=["alpha"],
    )

    assert keyword_variant.terms() == path_variant.terms()
    assert _variant_key(keyword_variant) != _variant_key(path_variant)


class ExplodingRewriteProvider(QueryRewriteProvider):
    provider_name = "exploding"

    def rewrite(self, plan):
        raise RuntimeError("boom")


def test_original_rewrite_result_wraps_provider_errors() -> None:
    plan = QueryUnderstanding().build_search_plan("AgentLoop 在哪里?")

    result = build_original_rewrite_result(plan, provider=ExplodingRewriteProvider())

    assert [variant.variant_id for variant in result.variants] == ["original"]
    assert result.fallback_reason == "RuntimeError"
    assert result.audit_summary()["rewrite_status"] == "fallback"
