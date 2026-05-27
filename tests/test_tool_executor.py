from app.rag.query_rewrite import QueryRewriteResult, QueryVariant
from app.rag.query_understanding import SearchPlan
from app.rag.repo_rag import Citation, RepoChunk, RetrievalResult
from app.tools.tool_executor import ToolExecutor


class VariantOnlyRewriteProvider:
    provider_name = "variant_only"

    def rewrite(self, plan: SearchPlan) -> QueryRewriteResult:
        original = QueryVariant(
            variant_id="original",
            query_text=plan.original_query,
            question_type=plan.question_type,
            keywords=plan.keywords,
            symbols=plan.symbols,
            path_hints=plan.path_hints,
            max_results=plan.max_results,
            retrieval_mode=plan.retrieval_mode,
        )
        usage = QueryVariant(
            variant_id="usage",
            query_text="usage replacement_token",
            question_type=plan.question_type,
            keywords=["replacement_token"],
            max_results=plan.max_results,
            retrieval_mode=plan.retrieval_mode,
        )
        return QueryRewriteResult(
            original_plan=plan,
            variants=[original, usage],
            provider_name=self.provider_name,
        )


class VariantOnlyRetriever:
    def __init__(self) -> None:
        self.queries: list[str] = []
        self.last_channel_summary: dict[str, int | float | str] = {}

    def retrieve(self, repo_path: str, plan: SearchPlan) -> list[RetrievalResult]:
        self.queries.append(plan.original_query)
        self.last_channel_summary = {
            "mode": "hybrid",
            "lexical_results": 0,
            "embedding_results": 0,
            "fused_results": 0,
            "min_fused_score": 0.35,
        }
        if plan.original_query != "usage replacement_token":
            return []

        self.last_channel_summary["lexical_results"] = 1
        self.last_channel_summary["fused_results"] = 1
        chunk = RepoChunk(
            chunk_id="app/service.py:1-1",
            file_path="app/service.py",
            start_line=1,
            end_line=1,
            text="def replacement_token(): pass",
        )
        return [
            RetrievalResult(
                chunk=chunk,
                citation=Citation("app/service.py", 1, 1),
                score=100,
            )
        ]


def test_tool_executor_keeps_variant_results_when_strong_original_has_no_hits() -> None:
    retriever = VariantOnlyRetriever()
    executor = ToolExecutor(
        repo_retriever=retriever,
        query_rewrite_provider=VariantOnlyRewriteProvider(),
    )
    plan = SearchPlan(
        original_query="MissingSymbol 在哪里实现?",
        question_type="implementation_explanation",
        keywords=[],
        symbols=["MissingSymbol"],
        path_hints=[],
        max_results=3,
        retrieval_mode="hybrid",
    )

    result = executor.search_repo_rag(
        repo_path=".",
        keyword="MissingSymbol",
        search_plan=plan,
    )

    assert result.error is None
    assert retriever.queries == ["MissingSymbol 在哪里实现?", "usage replacement_token"]
    assert [item["file_path"] for item in result.results] == ["app/service.py"]
    assert result.audit_summary["rewrite_provider"] == "variant_only"
