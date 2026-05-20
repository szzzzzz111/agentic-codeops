from pathlib import Path

from app.rag.query_understanding import QueryUnderstanding
from app.rag.repo_rag import LexicalRepoRetriever, chunk_repository


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
