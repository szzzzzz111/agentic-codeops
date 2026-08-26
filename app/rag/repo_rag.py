import hashlib
import math
import re
from dataclasses import dataclass
from pathlib import PurePosixPath

from app.rag.query_understanding import SearchPlan
from app.tools.file_tools import list_files, read_file

DEFAULT_LEXICAL_WEIGHT = 0.65
DEFAULT_EMBEDDING_WEIGHT = 0.35
DEFAULT_MIN_FUSED_SCORE = 0.35


@dataclass(frozen=True)
class HybridFusionSettings:
    lexical_weight: float = DEFAULT_LEXICAL_WEIGHT
    embedding_weight: float = DEFAULT_EMBEDDING_WEIGHT
    min_fused_score: float = DEFAULT_MIN_FUSED_SCORE

    def __post_init__(self) -> None:
        _validate_non_negative_finite(
            self.lexical_weight,
            field_name="lexical_weight",
        )
        _validate_non_negative_finite(
            self.embedding_weight,
            field_name="embedding_weight",
        )
        _validate_non_negative_finite(
            self.min_fused_score,
            field_name="min_fused_score",
        )
        if self.lexical_weight == 0 and self.embedding_weight == 0:
            raise ValueError("at least one fusion weight must be positive")


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


class DeterministicEmbeddingProvider:
    requires_external_service = False

    def __init__(self, *, dimensions: int = 32) -> None:
        if dimensions <= 0:
            raise ValueError("dimensions must be positive")
        self.dimensions = dimensions

    def embed(self, text: str) -> list[float]:
        vector = [0.0 for _ in range(self.dimensions)]
        for token in _tokenize_embedding_text(text):
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign

        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector
        return [value / norm for value in vector]


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


class EmbeddingRepoRetriever:
    def __init__(
        self,
        *,
        embedding_provider: DeterministicEmbeddingProvider | None = None,
        chunk_size: int = 8,
    ) -> None:
        self.embedding_provider = embedding_provider or DeterministicEmbeddingProvider()
        self.chunk_size = chunk_size

    def retrieve(self, repo_path: str, plan: SearchPlan) -> list[RetrievalResult]:
        query_vector = self.embedding_provider.embed(" ".join(plan.terms()) or plan.original_query)
        scored: list[RetrievalResult] = []
        for chunk in chunk_repository(repo_path, max_lines=self.chunk_size):
            score = _embedding_score(query_vector, self.embedding_provider.embed(_embedding_text(chunk)))
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

        scored.sort(key=lambda item: (-item.score, item.citation.file_path, item.citation.start_line))
        return _deduplicate(scored)[: plan.max_results]


class HybridRepoRetriever:
    def __init__(
        self,
        *,
        lexical_retriever: LexicalRepoRetriever | None = None,
        embedding_retriever: EmbeddingRepoRetriever | None = None,
        fusion_settings: HybridFusionSettings | None = None,
    ) -> None:
        self.lexical_retriever = lexical_retriever or LexicalRepoRetriever()
        self.embedding_retriever = embedding_retriever or EmbeddingRepoRetriever()
        self.fusion_settings = fusion_settings or DEFAULT_HYBRID_FUSION_SETTINGS
        self.last_channel_summary: dict[str, str | int | float] = {}

    def retrieve(self, repo_path: str, plan: SearchPlan) -> list[RetrievalResult]:
        lexical_results = self.lexical_retriever.retrieve(repo_path, plan)
        embedding_results = self.embedding_retriever.retrieve(repo_path, plan)
        raw_embedding_result_count = len(embedding_results)
        if _requires_lexical_anchor(plan):
            lexical_keys = {_citation_key(result.citation) for result in lexical_results}
            embedding_results = [
                result
                for result in embedding_results
                if _citation_key(result.citation) in lexical_keys
            ]
        fused_results = hybrid_fuse(
            lexical_results,
            embedding_results,
            max_results=plan.max_results,
            settings=self.fusion_settings,
        )
        self.last_channel_summary = {
            "mode": "hybrid",
            "lexical_results": len(lexical_results),
            "embedding_results": raw_embedding_result_count,
            "anchored_embedding_results": len(embedding_results),
            "fused_results": len(fused_results),
            "lexical_weight": self.fusion_settings.lexical_weight,
            "embedding_weight": self.fusion_settings.embedding_weight,
            "min_fused_score": self.fusion_settings.min_fused_score,
        }
        return fused_results


def hybrid_fuse(
    lexical_results: list[RetrievalResult],
    embedding_results: list[RetrievalResult],
    *,
    max_results: int,
    settings: HybridFusionSettings | None = None,
    lexical_weight: float = DEFAULT_LEXICAL_WEIGHT,
    embedding_weight: float = DEFAULT_EMBEDDING_WEIGHT,
    min_fused_score: float = DEFAULT_MIN_FUSED_SCORE,
) -> list[RetrievalResult]:
    effective_settings = settings or HybridFusionSettings(
        lexical_weight=lexical_weight,
        embedding_weight=embedding_weight,
        min_fused_score=min_fused_score,
    )
    lexical_max = max((result.score for result in lexical_results), default=0)
    embedding_max = max((result.score for result in embedding_results), default=0)
    fused: dict[tuple[str, int, int], tuple[RetrievalResult, float]] = {}

    for result in lexical_results:
        key = _citation_key(result.citation)
        fused[key] = (
            result,
            _normalized(result.score, lexical_max) * effective_settings.lexical_weight,
        )

    for result in embedding_results:
        key = _citation_key(result.citation)
        existing = fused.get(key)
        score = (
            _normalized(result.score, embedding_max)
            * effective_settings.embedding_weight
        )
        if existing:
            fused[key] = (existing[0], existing[1] + score)
        else:
            fused[key] = (result, score)

    results = [
        RetrievalResult(
            chunk=result.chunk,
            citation=result.citation,
            score=round(score * 1000),
        )
        for result, score in (item for item in fused.values())
        if score >= effective_settings.min_fused_score
    ]
    results.sort(key=lambda item: (-item.score, item.citation.file_path, item.citation.start_line))
    return results[:max_results]


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


def _tokenize_embedding_text(text: str) -> list[str]:
    return [token.lower() for token in re.findall(r"[A-Za-z0-9_]{2,}", text)]


def _embedding_text(chunk: RepoChunk) -> str:
    return f"{chunk.file_path}\n{chunk.text}"


def _embedding_score(left: list[float], right: list[float]) -> int:
    similarity = sum(left_value * right_value for left_value, right_value in zip(left, right))
    return round(max(0.0, similarity) * 100)


def _normalized(score: int, max_score: int) -> float:
    if max_score <= 0:
        return 0.0
    return score / max_score


def _validate_non_negative_finite(value: float, *, field_name: str) -> None:
    if (
        isinstance(value, bool)
        or not isinstance(value, int | float)
        or not math.isfinite(value)
        or value < 0
    ):
        raise ValueError(f"{field_name} must be a non-negative finite number")


DEFAULT_HYBRID_FUSION_SETTINGS = HybridFusionSettings()


def _citation_key(citation: Citation) -> tuple[str, int, int]:
    return (citation.file_path, citation.start_line, citation.end_line)


def _requires_lexical_anchor(plan: SearchPlan) -> bool:
    return bool(plan.path_hints or plan.symbols)


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
