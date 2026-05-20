from dataclasses import dataclass
from pathlib import PurePosixPath
import re

from app.rag.query_understanding import SearchPlan
from app.tools.file_tools import list_files, read_file


@dataclass(frozen=True)
class RepoChunk:
    chunk_id: str
    file_path: str
    start_line: int
    end_line: int
    text: str


@dataclass(frozen=True)
class Citation:
    file_path: str
    start_line: int
    end_line: int

    def label(self) -> str:
        return f"{self.file_path}:{self.start_line}-{self.end_line}"


@dataclass(frozen=True)
class RetrievalResult:
    chunk: RepoChunk
    citation: Citation
    score: int


class LexicalRepoRetriever:
    def __init__(self, *, chunk_size: int = 8) -> None:
        self.chunk_size = chunk_size

    def retrieve(self, repo_path: str, plan: SearchPlan) -> list[RetrievalResult]:
        scored: list[RetrievalResult] = []
        for chunk in chunk_repository(repo_path, max_lines=self.chunk_size):
            score = score_chunk(chunk, plan)
            if score <= 0:
                continue
            scored.append(
                RetrievalResult(
                    chunk=chunk,
                    citation=Citation(
                        file_path=chunk.file_path,
                        start_line=chunk.start_line,
                        end_line=chunk.end_line,
                    ),
                    score=score,
                )
            )

        scored.sort(key=lambda item: (-item.score, item.citation.file_path))
        return _deduplicate(scored)[: plan.max_results]


def chunk_repository(repo_path: str, *, max_lines: int = 8) -> list[RepoChunk]:
    chunks: list[RepoChunk] = []
    for file_path in list_files(repo_path):
        text = read_file(repo_path, file_path)
        lines = text.splitlines()
        for offset in range(0, len(lines), max_lines):
            chunk_lines = lines[offset : offset + max_lines]
            if not chunk_lines:
                continue
            start_line = offset + 1
            end_line = offset + len(chunk_lines)
            chunks.append(
                RepoChunk(
                    chunk_id=f"{file_path}:{start_line}-{end_line}",
                    file_path=file_path,
                    start_line=start_line,
                    end_line=end_line,
                    text="\n".join(chunk_lines),
                )
            )
    return chunks


def score_chunk(chunk: RepoChunk, plan: SearchPlan) -> int:
    score = 0
    lower_text = chunk.text.lower()
    lower_path = chunk.file_path.lower()
    filename = PurePosixPath(chunk.file_path).name.lower()

    for path_hint in plan.path_hints:
        hint = path_hint.lower()
        if hint == lower_path:
            score += 20
        elif hint in lower_path or hint in filename:
            score += 10

    for symbol in plan.symbols:
        if _contains_exact_token(chunk.text, symbol):
            score += 12
        elif symbol.lower() in lower_text:
            score += 6
        if symbol.lower() in lower_path:
            score += 5

    for keyword in plan.keywords:
        if _contains_exact_token(chunk.text, keyword):
            score += 4
        elif keyword.lower() in lower_text:
            score += 2
        if keyword.lower() in lower_path:
            score += 3

    return score


def _contains_exact_token(text: str, token: str) -> bool:
    return re.search(rf"(?<![A-Za-z0-9_]){re.escape(token)}(?![A-Za-z0-9_])", text) is not None


def _deduplicate(results: list[RetrievalResult]) -> list[RetrievalResult]:
    deduped: list[RetrievalResult] = []
    for result in results:
        if any(_overlaps_or_touches(result.citation, kept.citation) for kept in deduped):
            continue
        deduped.append(result)
    return deduped


def _overlaps_or_touches(left: Citation, right: Citation) -> bool:
    if left.file_path != right.file_path:
        return False
    return left.start_line <= right.end_line + 2 and right.start_line <= left.end_line + 2
