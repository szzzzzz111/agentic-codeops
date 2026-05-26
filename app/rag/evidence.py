from dataclasses import dataclass, field
import hashlib
from pathlib import PurePosixPath, PureWindowsPath


DEFAULT_MAX_CONTEXT_CHARS = 4000


@dataclass(frozen=True)
class ContextBudget:
    max_context_chars: int
    budget_used_chars: int
    budget_remaining_chars: int
    included_count: int
    omitted_count: int
    truncated_count: int


@dataclass(frozen=True)
class EvidenceItem:
    evidence_id: str
    file_path: str
    start_line: int
    end_line: int
    score: int
    snippet: str
    source_summary: str
    included: bool
    truncated: bool


@dataclass(frozen=True)
class EvidencePack:
    original_query: str
    question_type: str
    retrieval_mode: str
    budget: ContextBudget
    items: list[EvidenceItem] = field(default_factory=list)

    def audit_summary(self) -> dict[str, int]:
        return {
            "evidence_items": len(self.items),
            "included_count": self.budget.included_count,
            "omitted_count": self.budget.omitted_count,
            "truncated_count": self.budget.truncated_count,
            "budget_used_chars": self.budget.budget_used_chars,
            "max_context_chars": self.budget.max_context_chars,
        }


def build_evidence_pack(
    results: list[dict[str, str | int]],
    *,
    original_query: str,
    question_type: str,
    retrieval_mode: str,
    max_context_chars: int = DEFAULT_MAX_CONTEXT_CHARS,
) -> EvidencePack:
    if max_context_chars < 0:
        raise ValueError("max_context_chars must be non-negative")

    remaining = max_context_chars
    items: list[EvidenceItem] = []
    included_count = 0
    omitted_count = 0
    truncated_count = 0

    for result in results:
        file_path = result.get("file_path")
        if not isinstance(file_path, str) or _is_absolute_path(file_path):
            continue

        start_line = _coerce_int(result.get("start_line", result.get("line_number")))
        end_line = _coerce_int(result.get("end_line", start_line))
        score = _coerce_int(result.get("score"))
        original_snippet = str(result.get("line_text", "")).strip()
        snippet = ""
        included = False
        truncated = False

        if remaining > 0 and len(original_snippet) <= remaining:
            snippet = original_snippet
            remaining -= len(snippet)
            included = True
            included_count += 1
        elif remaining > 0:
            snippet = original_snippet[:remaining]
            remaining = 0
            included = True
            truncated = True
            included_count += 1
            truncated_count += 1
        else:
            omitted_count += 1

        items.append(
            EvidenceItem(
                evidence_id=_stable_evidence_id(
                    file_path=file_path,
                    start_line=start_line,
                    end_line=end_line,
                    score=score,
                    snippet=original_snippet,
                ),
                file_path=file_path,
                start_line=start_line,
                end_line=end_line,
                score=score,
                snippet=snippet,
                source_summary=f"repo_rag:{retrieval_mode}",
                included=included,
                truncated=truncated,
            )
        )

    budget_used_chars = max_context_chars - remaining
    return EvidencePack(
        original_query=original_query,
        question_type=question_type,
        retrieval_mode=retrieval_mode,
        budget=ContextBudget(
            max_context_chars=max_context_chars,
            budget_used_chars=budget_used_chars,
            budget_remaining_chars=remaining,
            included_count=included_count,
            omitted_count=omitted_count,
            truncated_count=truncated_count,
        ),
        items=items,
    )


def _stable_evidence_id(
    *,
    file_path: str,
    start_line: int,
    end_line: int,
    score: int,
    snippet: str,
) -> str:
    raw = f"{file_path}:{start_line}:{end_line}:{score}:{snippet}"
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]
    return f"ev_{digest}"


def _coerce_int(value: object) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return 0


def _is_absolute_path(file_path: str) -> bool:
    return PureWindowsPath(file_path).is_absolute() or PurePosixPath(
        file_path
    ).is_absolute()
