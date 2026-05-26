from dataclasses import dataclass, field

from app.rag.evidence import EvidencePack, build_evidence_pack
from app.rag.query_understanding import SearchPlan
from app.rag.repo_rag import HybridRepoRetriever
from app.tools.file_tools import search_code


@dataclass(frozen=True)
class ToolExecutionResult:
    tool_name: str
    parameters: dict[str, str]
    results: list[dict[str, str | int]] = field(default_factory=list)
    error: str | None = None
    audit_summary: dict[str, str | int | float] = field(default_factory=dict)
    evidence_pack: EvidencePack | None = None

    def call_summary(self) -> dict[str, str]:
        summary = {
            "tool_name": self.tool_name,
            **self.parameters,
            "status": "error" if self.error else "success",
            "result_count": str(len(self.results)),
        }
        if self.error:
            summary["error"] = self.error
        return summary


class ToolExecutor:
    def __init__(self, repo_retriever: HybridRepoRetriever | None = None) -> None:
        self.repo_retriever = repo_retriever or HybridRepoRetriever()

    def search_code(
        self,
        repo_path: str,
        keyword: str,
        max_results: int = 20,
    ) -> ToolExecutionResult:
        try:
            results = search_code(
                repo_path=repo_path,
                keyword=keyword,
                max_results=max_results,
            )
        except (NotADirectoryError, OSError, ValueError) as exc:
            return ToolExecutionResult(
                tool_name="search_code",
                parameters={"keyword": keyword},
                error=type(exc).__name__,
            )

        return ToolExecutionResult(
            tool_name="search_code",
            parameters={"keyword": keyword},
            results=results,
        )

    def search_repo_rag(
        self,
        repo_path: str,
        keyword: str,
        search_plan: SearchPlan,
    ) -> ToolExecutionResult:
        parameters = {
            "keyword": keyword,
            "question_type": search_plan.question_type,
            "retrieval_mode": search_plan.retrieval_mode,
        }
        try:
            results = [
                {
                    "file_path": result.citation.file_path,
                    "line_number": result.citation.start_line,
                    "line_text": result.chunk.text.strip(),
                    "start_line": result.citation.start_line,
                    "end_line": result.citation.end_line,
                    "score": result.score,
                }
                for result in self.repo_retriever.retrieve(repo_path, search_plan)
            ]
        except (NotADirectoryError, OSError, ValueError) as exc:
            return ToolExecutionResult(
                tool_name="repo_rag",
                parameters=parameters,
                error=type(exc).__name__,
            )

        evidence_pack = build_evidence_pack(
            results,
            original_query=search_plan.original_query,
            question_type=search_plan.question_type,
            retrieval_mode=search_plan.retrieval_mode,
        )
        audit_summary = {
            **getattr(self.repo_retriever, "last_channel_summary", {}),
            **evidence_pack.audit_summary(),
        }

        return ToolExecutionResult(
            tool_name="repo_rag",
            parameters=parameters,
            results=results,
            audit_summary=audit_summary,
            evidence_pack=evidence_pack,
        )
