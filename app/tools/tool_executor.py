from dataclasses import dataclass, field

from app.rag.evidence import EvidencePack, build_evidence_pack
from app.rag.query_understanding import SearchPlan
from app.rag.query_rewrite import (
    DeterministicQueryRewriteProvider,
    QueryRewriteProvider,
    build_original_rewrite_result,
)
from app.rag.rerank import (
    DeterministicRepoReranker,
    RepoReranker,
    rerank_with_fallback,
)
from app.rag.repo_rag import HybridRepoRetriever, RetrievalResult
from app.patching.apply import PatchApplyResult, apply_unified_diff
from app.tools.file_tools import search_code
from app.verification.runner import run_whitelisted_verification
from app.worktrees.manager import WorktreeCreateResult, WorktreeManager
from app.worktrees.disposal import WorktreeDisposalResult


@dataclass(frozen=True)
class ToolExecutionResult:
    tool_name: str
    parameters: dict[str, str]
    results: list[dict[str, str | int]] = field(default_factory=list)
    error: str | None = None
    audit_summary: dict[str, str | int | float] = field(default_factory=dict)
    evidence_pack: EvidencePack | None = None
    patch_apply_result: PatchApplyResult | None = None
    worktree_create_result: WorktreeCreateResult | None = None
    worktree_disposal_result: WorktreeDisposalResult | None = None

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
    def __init__(
        self,
        repo_retriever: HybridRepoRetriever | None = None,
        query_rewrite_provider: QueryRewriteProvider | None = None,
        reranker: RepoReranker | None = None,
        worktree_manager: WorktreeManager | None = None,
    ) -> None:
        self.repo_retriever = repo_retriever or HybridRepoRetriever()
        self.query_rewrite_provider = (
            query_rewrite_provider or DeterministicQueryRewriteProvider()
        )
        self.reranker = reranker or DeterministicRepoReranker()
        self.worktree_manager = worktree_manager or WorktreeManager()

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
            rewrite_result = build_original_rewrite_result(
                search_plan,
                provider=self.query_rewrite_provider,
            )
            retrieval_results = []
            original_result_keys: set[tuple[str, int, int]] = set()
            aggregate_channel_summary: dict[str, str | int | float] = {}
            for variant in rewrite_result.variants:
                variant_results = self.repo_retriever.retrieve(
                    repo_path,
                    variant.to_search_plan(),
                )
                channel_summary = getattr(
                    self.repo_retriever,
                    "last_channel_summary",
                    {},
                )
                if channel_summary:
                    if not aggregate_channel_summary:
                        aggregate_channel_summary = {
                            "mode": search_plan.retrieval_mode,
                            "lexical_results": 0,
                            "embedding_results": 0,
                            "anchored_embedding_results": 0,
                            "fused_results": 0,
                            "min_fused_score": channel_summary.get(
                                "min_fused_score",
                                0.35,
                            ),
                        }
                    aggregate_channel_summary["lexical_results"] = int(
                        aggregate_channel_summary["lexical_results"]
                    ) + int(channel_summary.get("lexical_results", 0))
                    aggregate_channel_summary["embedding_results"] = int(
                        aggregate_channel_summary["embedding_results"]
                    ) + int(channel_summary.get("embedding_results", 0))
                    aggregate_channel_summary["anchored_embedding_results"] = int(
                        aggregate_channel_summary["anchored_embedding_results"]
                    ) + int(channel_summary.get("anchored_embedding_results", 0))
                    aggregate_channel_summary["fused_results"] = int(
                        aggregate_channel_summary["fused_results"]
                    ) + int(channel_summary.get("fused_results", len(variant_results)))
                for result in variant_results:
                    key = _citation_key(result)
                    if variant.variant_id == "original":
                        original_result_keys.add(key)
                    retrieval_results.append(result)

            merged_results = _merge_retrieval_results(retrieval_results)
            rerank_result = rerank_with_fallback(
                merged_results,
                plan=search_plan,
                original_result_keys=original_result_keys,
                max_results=search_plan.max_results,
                reranker=self.reranker,
            )
            results = [
                {
                    "file_path": result.citation.file_path,
                    "line_number": result.citation.start_line,
                    "line_text": result.chunk.text.strip(),
                    "start_line": result.citation.start_line,
                    "end_line": result.citation.end_line,
                    "score": result.score,
                }
                for result in rerank_result.results
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
            **aggregate_channel_summary,
            "merged_results": len(merged_results),
            **rewrite_result.audit_summary(),
            **rerank_result.audit_summary(),
            **evidence_pack.audit_summary(),
        }

        return ToolExecutionResult(
            tool_name="repo_rag",
            parameters=parameters,
            results=results,
            audit_summary=audit_summary,
            evidence_pack=evidence_pack,
        )

    def patch_apply(self, repo_path: str, diff_text: str) -> ToolExecutionResult:
        result = apply_unified_diff(repo_path, diff_text)
        if not result.applied:
            return ToolExecutionResult(
                tool_name="patch_apply",
                parameters={},
                error=result.error or "PatchApplyError",
                audit_summary={"changed_files": 0},
                patch_apply_result=result,
            )
        return ToolExecutionResult(
            tool_name="patch_apply",
            parameters={},
            results=[{"file_path": path, "line_number": 0, "line_text": ""} for path in result.changed_files],
            audit_summary={"changed_files": len(result.changed_files)},
            patch_apply_result=result,
        )

    def worktree_create(
        self,
        repo_path: str,
        user_id: str,
        patch_id: str,
    ) -> ToolExecutionResult:
        result = self.worktree_manager.create(
            repo_path=repo_path,
            user_id=user_id,
            patch_id=patch_id,
        )
        return ToolExecutionResult(
            tool_name="worktree_create",
            parameters={"worktree_id": result.worktree_id} if result.worktree_id else {},
            error=None if result.created else result.reason,
            audit_summary={"status": result.status},
            worktree_create_result=result,
        )

    def worktree_dispose(
        self,
        repo_path: str,
        user_id: str,
        worktree_id: str,
        attempt_kind: str,
    ) -> ToolExecutionResult:
        result = self.worktree_manager.dispose(
            repo_path=repo_path,
            user_id=user_id,
            worktree_id=worktree_id,
            attempt_kind=attempt_kind,
        )
        return ToolExecutionResult(
            tool_name="worktree_dispose",
            parameters={
                "worktree_id": result.worktree_id,
                "attempt_kind": result.attempt_kind,
                "completed_step": result.completed_step or "none",
            },
            error=None if result.succeeded else result.reason,
            audit_summary={
                "preflight_classification": result.preflight_classification,
                "completed_step": result.completed_step,
                "failed_step": result.failed_step,
            },
            worktree_disposal_result=result,
        )
    def verification_run(self, repo_path: str, command_label: str) -> ToolExecutionResult:
        result = run_whitelisted_verification(repo_path, command_label)
        parameters = {
            "command_label": result.command_label,
            "exit_code": "" if result.exit_code is None else str(result.exit_code),
            "duration_ms": str(result.duration_ms),
            "timed_out": str(result.timed_out).lower(),
            "truncated": str(result.truncated).lower(),
        }
        error = result.status if result.status in {"rejected", "unavailable"} else None
        return ToolExecutionResult(
            tool_name="verification_run",
            parameters=parameters,
            error=error,
            audit_summary=result.audit_summary(),
        )


def _citation_key(result: RetrievalResult) -> tuple[str, int, int]:
    return (
        result.citation.file_path,
        result.citation.start_line,
        result.citation.end_line,
    )


def _merge_retrieval_results(
    results: list[RetrievalResult],
) -> list[RetrievalResult]:
    merged: dict[tuple[str, int, int], RetrievalResult] = {}
    for result in results:
        key = _citation_key(result)
        existing = merged.get(key)
        if existing is None or result.score > existing.score:
            merged[key] = result
    return sorted(
        merged.values(),
        key=lambda item: (-item.score, item.citation.file_path, item.citation.start_line),
    )
