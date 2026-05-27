from pathlib import Path

from app.rag.query_understanding import QueryUnderstanding
from app.rag.repo_rag import (
    Citation,
    DeterministicEmbeddingProvider,
    EmbeddingRepoRetriever,
    HybridRepoRetriever,
    LexicalRepoRetriever,
    RepoChunk,
    RetrievalResult,
    chunk_repository,
    hybrid_fuse,
)


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_chunk_repository_returns_line_citation_chunks(tmp_path: Path) -> None:
    write_text(
        tmp_path / "app" / "service.py",
        "class PaymentService:\n"
        "    def charge(self):\n"
        "        return 'ok'\n",
    )

    chunks = chunk_repository(str(tmp_path), max_lines=2)

    assert chunks[0].chunk_id == "app/service.py:1-2"
    assert chunks[0].file_path == "app/service.py"
    assert chunks[0].start_line == 1
    assert chunks[0].end_line == 2
    assert "PaymentService" in chunks[0].text


def test_lexical_retriever_prioritizes_symbol_and_path_matches(
    tmp_path: Path,
) -> None:
    write_text(
        tmp_path / "app" / "harness" / "kernel.py",
        "class AgentLoop:\n"
        "    def run(self):\n"
        "        return search_code('needle')\n",
    )
    write_text(
        tmp_path / "docs" / "notes.md",
        "This note mentions run and search but not the target symbol.\n",
    )
    plan = QueryUnderstanding().build_search_plan(
        "AgentLoop 在 app/harness/kernel.py 怎么调用 search_code?"
    )

    results = LexicalRepoRetriever().retrieve(str(tmp_path), plan)

    assert results[0].citation.file_path == "app/harness/kernel.py"
    assert results[0].citation.start_line == 1
    assert results[0].citation.end_line >= 2
    assert results[0].score > 0


def test_lexical_retriever_deduplicates_by_file_and_line_window(
    tmp_path: Path,
) -> None:
    write_text(
        tmp_path / "app.py",
        "def search_code():\n"
        "    return 'search_code'\n"
        "search_code()\n",
    )
    plan = QueryUnderstanding().build_search_plan("search_code 在哪里?")

    results = LexicalRepoRetriever(chunk_size=1).retrieve(str(tmp_path), plan)

    assert [result.citation.file_path for result in results] == ["app.py"]


def test_lexical_retriever_keeps_non_overlapping_chunks_in_same_file(
    tmp_path: Path,
) -> None:
    write_text(
        tmp_path / "app.py",
        "def first_search_code():\n"
        "    return 'search_code first'\n"
        "\n"
        "\n"
        "def second_search_code():\n"
        "    return 'search_code second'\n",
    )
    plan = QueryUnderstanding().build_search_plan("search_code 在哪里?")

    results = LexicalRepoRetriever(chunk_size=2).retrieve(str(tmp_path), plan)

    assert [result.citation.start_line for result in results] == [1, 5]


def test_deterministic_embedding_provider_returns_stable_fixed_vectors() -> None:
    provider = DeterministicEmbeddingProvider(dimensions=16)

    first = provider.embed("AgentLoop calls search_code")
    second = provider.embed("AgentLoop calls search_code")

    assert first == second
    assert len(first) == 16
    assert all(isinstance(value, float) for value in first)
    assert provider.requires_external_service is False


def test_embedding_retriever_returns_relative_citations(tmp_path: Path) -> None:
    write_text(
        tmp_path / "app" / "payments.py",
        "class PaymentProcessor:\n"
        "    def capture_invoice(self):\n"
        "        return 'invoice captured'\n",
    )
    plan = QueryUnderstanding().build_search_plan("How does capture_invoice work?")

    results = EmbeddingRepoRetriever().retrieve(str(tmp_path), plan)

    assert results
    assert results[0].citation.file_path == "app/payments.py"
    assert results[0].citation.start_line == 1
    assert results[0].citation.end_line >= 2
    assert not Path(results[0].citation.file_path).is_absolute()


def test_hybrid_fusion_merges_duplicate_chunks_and_keeps_stable_order() -> None:
    first_chunk = RepoChunk(
        chunk_id="app/service.py:1-2",
        file_path="app/service.py",
        start_line=1,
        end_line=2,
        text="class PaymentService:\n    pass",
    )
    second_chunk = RepoChunk(
        chunk_id="docs/service.md:1-1",
        file_path="docs/service.md",
        start_line=1,
        end_line=1,
        text="Payment service overview",
    )
    lexical = [
        RetrievalResult(
            chunk=first_chunk,
            citation=Citation("app/service.py", 1, 2),
            score=20,
        ),
        RetrievalResult(
            chunk=second_chunk,
            citation=Citation("docs/service.md", 1, 1),
            score=10,
        )
    ]
    embedding = [
        RetrievalResult(
            chunk=first_chunk,
            citation=Citation("app/service.py", 1, 2),
            score=60,
        ),
        RetrievalResult(
            chunk=second_chunk,
            citation=Citation("docs/service.md", 1, 1),
            score=60,
        ),
    ]

    results = hybrid_fuse(lexical, embedding, max_results=4)

    assert [result.citation.file_path for result in results] == [
        "app/service.py",
        "docs/service.md",
    ]
    assert results[0].score > results[1].score


def test_hybrid_fusion_filters_results_below_minimum_score() -> None:
    weak_chunk = RepoChunk(
        chunk_id="docs/weak.md:1-1",
        file_path="docs/weak.md",
        start_line=1,
        end_line=1,
        text="Barely related note",
    )
    embedding = [
        RetrievalResult(
            chunk=weak_chunk,
            citation=Citation("docs/weak.md", 1, 1),
            score=10,
        )
    ]

    results = hybrid_fuse([], embedding, max_results=4, min_fused_score=0.5)

    assert results == []


def test_hybrid_fusion_keeps_embedding_only_results_by_default() -> None:
    semantic_chunk = RepoChunk(
        chunk_id="docs/semantic.md:1-1",
        file_path="docs/semantic.md",
        start_line=1,
        end_line=1,
        text="Semantic match without lexical overlap",
    )
    embedding = [
        RetrievalResult(
            chunk=semantic_chunk,
            citation=Citation("docs/semantic.md", 1, 1),
            score=100,
        )
    ]

    results = hybrid_fuse([], embedding, max_results=4)

    assert [result.citation.file_path for result in results] == ["docs/semantic.md"]
    assert results[0].score == 350


def test_hybrid_retriever_requires_lexical_anchor_for_symbol_queries(
    tmp_path: Path,
) -> None:
    write_text(tmp_path / "app.py", "print('ok')\n")
    plan = QueryUnderstanding().build_search_plan("帮我分析 UNIQUE_BUG_TOKEN")

    results = HybridRepoRetriever().retrieve(str(tmp_path), plan)

    assert results == []
    assert plan.symbols == ["UNIQUE_BUG_TOKEN"]


def test_hybrid_retriever_keeps_symbol_results_when_lexical_anchor_exists(
    tmp_path: Path,
) -> None:
    write_text(tmp_path / "app.py", "UNIQUE_BUG_TOKEN = True\n")
    plan = QueryUnderstanding().build_search_plan("帮我分析 UNIQUE_BUG_TOKEN")

    results = HybridRepoRetriever().retrieve(str(tmp_path), plan)

    assert [result.citation.file_path for result in results] == ["app.py"]
