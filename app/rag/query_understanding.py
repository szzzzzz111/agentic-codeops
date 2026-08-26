import re
from dataclasses import dataclass, field

QUESTION_CODE_LOCATION = "code_location"
QUESTION_IMPLEMENTATION_EXPLANATION = "implementation_explanation"
QUESTION_CALL_RELATIONSHIP = "call_relationship"
QUESTION_TEST_OR_VALIDATION = "test_or_validation"
QUESTION_FILE_SUMMARY = "file_summary"
QUESTION_UNKNOWN = "unknown"

DEFAULT_MAX_RESULTS = 8
RETRIEVAL_LEXICAL = "lexical"
RETRIEVAL_HYBRID = "hybrid"

PATH_PATTERN = re.compile(
    r"(?:[A-Za-z0-9_\-]+[\\/])+[A-Za-z0-9_\-.]+\.[A-Za-z0-9]+|"
    r"[A-Za-z0-9_\-]+\.[A-Za-z0-9]+"
)
SYMBOL_PATTERN = re.compile(
    r"\b[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z0-9_]+)*\b"
)
STOPWORDS = {
    "the",
    "and",
    "for",
    "with",
    "this",
    "that",
    "where",
    "what",
    "how",
    "why",
    "does",
    "from",
    "into",
    "repo",
    "project",
    "embedding",
    "vector",
}


@dataclass(frozen=True)
class SearchPlan:
    original_query: str
    question_type: str
    keywords: list[str] = field(default_factory=list)
    symbols: list[str] = field(default_factory=list)
    path_hints: list[str] = field(default_factory=list)
    max_results: int = DEFAULT_MAX_RESULTS
    retrieval_mode: str = RETRIEVAL_HYBRID

    def terms(self) -> list[str]:
        return _unique([*self.path_hints, *self.symbols, *self.keywords])


class QueryUnderstanding:
    def build_search_plan(self, message: str) -> SearchPlan:
        path_hints = _extract_paths(message)
        symbols = _extract_symbols(message, path_hints)
        keywords = _extract_keywords(message, symbols, path_hints)
        return SearchPlan(
            original_query=message,
            question_type=_classify_question(message, path_hints, symbols),
            keywords=keywords,
            symbols=symbols,
            path_hints=path_hints,
        )


def _extract_paths(message: str) -> list[str]:
    return _unique(match.replace("\\", "/") for match in PATH_PATTERN.findall(message))


def _extract_symbols(message: str, path_hints: list[str]) -> list[str]:
    path_parts: set[str] = set()
    for path in path_hints:
        path_parts.update(part for part in re.split(r"[/.\\-]", path) if part)

    symbols: list[str] = []
    for token in SYMBOL_PATTERN.findall(message):
        if token in path_parts:
            continue
        if token.lower() in STOPWORDS:
            continue
        if _looks_like_symbol(token):
            symbols.append(token)
    return _unique(symbols)


def _extract_keywords(
    message: str,
    symbols: list[str],
    path_hints: list[str],
) -> list[str]:
    excluded = {item.lower() for item in [*symbols, *path_hints]}
    words = re.findall(r"[A-Za-z][A-Za-z0-9_\-]{2,}", message)
    keywords = [
        word
        for word in words
        if word.lower() not in STOPWORDS and word.lower() not in excluded
    ]
    return _unique(keywords)


def _classify_question(
    message: str,
    path_hints: list[str],
    symbols: list[str],
) -> str:
    lower = message.lower()
    if any(term in message for term in ("测试", "验证", "校验")) or any(
        term in lower for term in ("test", "pytest", "verify", "validation")
    ):
        return QUESTION_TEST_OR_VALIDATION
    if any(term in message for term in ("怎么", "如何")) and "调用" in message:
        return QUESTION_IMPLEMENTATION_EXPLANATION
    if any(term in message for term in ("调用", "依赖", "关系")) or any(
        term in lower for term in ("call", "caller", "callee", "depend")
    ):
        return QUESTION_CALL_RELATIONSHIP
    if any(term in message for term in ("哪里", "哪个文件", "在哪", "定位")) or any(
        term in lower for term in ("where", "locate", "find")
    ):
        return QUESTION_CODE_LOCATION
    if any(term in message for term in ("总结", "概览", "摘要")) or any(
        term in lower for term in ("summary", "summarize", "overview")
    ):
        return QUESTION_FILE_SUMMARY
    if path_hints or symbols:
        return QUESTION_IMPLEMENTATION_EXPLANATION
    return QUESTION_UNKNOWN


def _looks_like_symbol(token: str) -> bool:
    return (
        "_" in token
        or "." in token
        or token.endswith("Error")
        or token[:1].isupper()
        or bool(re.search(r"[a-z][A-Z]", token))
    )


def _unique(values) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        if not value or value in seen:
            continue
        result.append(value)
        seen.add(value)
    return result
