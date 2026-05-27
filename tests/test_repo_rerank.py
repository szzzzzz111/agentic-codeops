from app.rag.query_understanding import QueryUnderstanding
from app.rag.rerank import (
    DeterministicRepoReranker,
    RepoReranker,
    rerank_with_fallback,
)
from app.rag.repo_rag import Citation, RepoChunk, RetrievalResult


def _result(
    file_path: str,
    text: str,
    *,
    score: int = 100,
    start_line: int = 1,
) -> RetrievalResult:
    chunk = RepoChunk(
        chunk_id=f"{file_path}:{start_line}-{start_line}",
        file_path=file_path,
        start_line=start_line,
        end_line=start_line,
        text=text,
    )
    return RetrievalResult(
        chunk=chunk,
        citation=Citation(file_path, start_line, start_line),
        score=score,
    )


def test_deterministic_rerank_preserves_original_direct_hits_and_limits_results() -> None:
    plan = QueryUnderstanding().build_search_plan(
        "AgentLoop 在 app/harness/kernel.py 怎么调用 search_code?"
    )
    original_hit = _result(
        "app/harness/kernel.py",
        "class AgentLoop:\n    def run(self): return search_code()",
        score=200,
    )
    variant_only = _result(
        "tests/test_agent_harness_kernel.py",
        "def test_agent_loop_records_query_understanding(): pass",
        score=900,
    )

    result = DeterministicRepoReranker().rerank(
        [variant_only, original_hit],
        plan=plan,
        original_result_keys={
            (
                original_hit.citation.file_path,
                original_hit.citation.start_line,
                original_hit.citation.end_line,
            )
        },
        max_results=1,
    )

    assert result.results == [original_hit]
    assert result.audit_summary() == {
        "rerank_provider": "deterministic",
        "rerank_status": "success",
        "rerank_input_count": 2,
        "rerank_output_count": 1,
    }


class ExplodingReranker(RepoReranker):
    provider_name = "exploding"

    def rerank(self, results, *, plan, original_result_keys, max_results):
        raise RuntimeError("boom")


def test_rerank_with_fallback_returns_unranked_results_on_error() -> None:
    plan = QueryUnderstanding().build_search_plan("AgentLoop 在哪里?")
    first = _result("app/a.py", "class AgentLoop: pass", score=10)
    second = _result("app/b.py", "class Other: pass", score=20)

    result = rerank_with_fallback(
        [first, second],
        plan=plan,
        original_result_keys=set(),
        max_results=1,
        reranker=ExplodingReranker(),
    )

    assert result.results == [first]
    assert result.fallback_reason == "RuntimeError"
    assert result.audit_summary()["rerank_status"] == "fallback"
