from dataclasses import dataclass, field
from pathlib import PurePosixPath, PureWindowsPath
import re

from app.rag.query_understanding import QueryUnderstanding, SearchPlan
from app.rag.repo_rag import HybridRepoRetriever
from app.tools.tool_executor import ToolExecutor


TOKEN_PATTERN = re.compile(r"[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z0-9_]+)*")
ALLOWED_TOOL_RISK = "low"
DENY_ANSWER = "仓库工具未通过权限策略校验，因此本次没有执行仓库工具。"
ASK_ANSWER = "工具调用需要人工审批，因此本次没有执行仓库工具。"
NO_TOOL_ANSWER = "未提取到可搜索关键词，因此没有调用仓库工具。"
CAPABILITY_STATUS_KEYWORD = "capability_status"


@dataclass(frozen=True)
class AgentLoopRequest:
    message: str
    repo_path: str
    trace_id: str


@dataclass(frozen=True)
class RouteDecision:
    route: str
    keyword: str | None
    reason: str


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    read_only: bool
    risk: str
    requires_approval: bool = False


@dataclass(frozen=True)
class PermissionDecision:
    tool_name: str
    status: str
    reason: str


@dataclass(frozen=True)
class TraceEvent:
    event_type: str
    tool_name: str | None = None
    status: str = "ok"
    summary: str = ""


@dataclass(frozen=True)
class AgentLoopResult:
    answer: str
    related_files: list[str] = field(default_factory=list)
    tool_calls: list[dict[str, str]] = field(default_factory=list)
    trace_events_internal: list[TraceEvent] = field(default_factory=list)

    def to_agent_result(self) -> dict[str, str | list[str] | list[dict[str, str]]]:
        return {
            "answer": self.answer,
            "related_files": self.related_files,
            "tool_calls": self.tool_calls,
        }


class RequestRouter:
    def route(self, message: str) -> RouteDecision:
        if _asks_about_unimplemented_vector_stack(message):
            return RouteDecision(
                route="repo_search",
                keyword=CAPABILITY_STATUS_KEYWORD,
                reason="capability_status_question",
            )
        keyword = _extract_search_keyword(message)
        if keyword:
            return RouteDecision(
                route="repo_search",
                keyword=keyword,
                reason="searchable_token",
            )
        return RouteDecision(
            route="chat_only",
            keyword=None,
            reason="no_searchable_token",
        )


class ToolRegistry:
    def __init__(self, specs: list[ToolSpec] | None = None) -> None:
        self._specs = {spec.name: spec for spec in specs or []}

    @classmethod
    def with_default_tools(cls) -> "ToolRegistry":
        return cls(
            [
                ToolSpec(
                    name="search_code",
                    description="Search code in a repository using a read-only tool.",
                    read_only=True,
                    risk=ALLOWED_TOOL_RISK,
                )
            ]
        )

    def get(self, name: str) -> ToolSpec | None:
        return self._specs.get(name)


class PermissionPolicy:
    def decide(
        self,
        tool_spec: ToolSpec | None,
        tool_name: str = "search_code",
    ) -> PermissionDecision:
        if tool_spec is None:
            return PermissionDecision(
                tool_name=tool_name,
                status="deny",
                reason="not_registered",
            )
        if not tool_spec.read_only:
            return PermissionDecision(
                tool_name=tool_spec.name,
                status="deny",
                reason="not_read_only",
            )
        if tool_spec.risk != ALLOWED_TOOL_RISK:
            return PermissionDecision(
                tool_name=tool_spec.name,
                status="deny",
                reason="risk_not_allowed",
            )
        if tool_spec.requires_approval:
            return PermissionDecision(
                tool_name=tool_spec.name,
                status="ask",
                reason="approval_required",
            )
        return PermissionDecision(
            tool_name=tool_spec.name,
            status="allow",
            reason="allowed",
        )


class ApprovalGate:
    def evaluate(self, decision: PermissionDecision) -> bool:
        return decision.status == "allow"


class AgentLoop:
    def __init__(
        self,
        *,
        router: RequestRouter | None = None,
        tool_registry: ToolRegistry | None = None,
        tool_executor: ToolExecutor | None = None,
        permission_policy: PermissionPolicy | None = None,
        approval_gate: ApprovalGate | None = None,
        query_understanding: QueryUnderstanding | None = None,
        repo_retriever: HybridRepoRetriever | None = None,
    ) -> None:
        self.router = router or RequestRouter()
        self.tool_registry = tool_registry or ToolRegistry.with_default_tools()
        self.tool_executor = tool_executor or ToolExecutor(repo_retriever=repo_retriever)
        self.permission_policy = permission_policy or PermissionPolicy()
        self.approval_gate = approval_gate or ApprovalGate()
        self.query_understanding = query_understanding or QueryUnderstanding()

    def run(self, request: AgentLoopRequest) -> AgentLoopResult:
        decision = self.router.route(request.message)
        trace_events = [
            TraceEvent(
                event_type="request_routed",
                status="ok",
                summary=f"route={decision.route}; reason={decision.reason}",
            )
        ]

        if decision.route != "repo_search" or not decision.keyword:
            return AgentLoopResult(
                answer=NO_TOOL_ANSWER,
                trace_events_internal=trace_events,
            )

        search_plan = self.query_understanding.build_search_plan(request.message)
        if _should_record_query_understanding(search_plan):
            trace_events.append(
                TraceEvent(
                    event_type="query_understood",
                    status="ok",
                    summary=(
                        f"question_type={search_plan.question_type}; "
                        f"mode={search_plan.retrieval_mode}; "
                        f"terms={len(search_plan.terms())}"
                    ),
                )
            )

        if _asks_about_unimplemented_vector_stack(request.message):
            return AgentLoopResult(
                answer=(
                    "V9 规划提供轻量 embedding retrieval 和 hybrid search；"
                    "当前未默认接入 Milvus、Elasticsearch、PgVector、Qdrant、"
                    "真实外部 embedding 服务或 memory。"
                ),
                trace_events_internal=trace_events,
            )

        tool_spec = self.tool_registry.get("search_code")
        permission_decision = self.permission_policy.decide(
            tool_spec,
            tool_name="search_code",
        )
        trace_events.append(
            TraceEvent(
                event_type="permission_checked",
                tool_name="search_code",
                status="ok" if permission_decision.status == "allow" else "error",
                summary=(
                    "tool=search_code; "
                    f"decision={permission_decision.status}; "
                    f"reason={permission_decision.reason}"
                ),
            )
        )

        if permission_decision.status == "deny":
            return AgentLoopResult(
                answer=DENY_ANSWER,
                trace_events_internal=[
                    *trace_events,
                    TraceEvent(
                        event_type="tool_rejected",
                        tool_name="search_code",
                        status="error",
                        summary=(
                            "tool=search_code rejected by permission policy; "
                            f"reason={permission_decision.reason}"
                        ),
                    ),
                ],
            )

        if not self.approval_gate.evaluate(permission_decision):
            return AgentLoopResult(
                answer=ASK_ANSWER,
                trace_events_internal=[
                    *trace_events,
                    TraceEvent(
                        event_type="approval_required",
                        tool_name="search_code",
                        status="ok",
                        summary="tool=search_code requires approval",
                    ),
                ],
            )

        trace_events.append(
            TraceEvent(
                event_type="tool_call",
                tool_name="repo_rag",
                status="ok",
                summary=f"tool=repo_rag; keyword={decision.keyword}",
            )
        )
        tool_result = self._run_repo_rag(
            repo_path=request.repo_path,
            keyword=decision.keyword,
            search_plan=search_plan,
        )
        related_files = _unique_related_files(tool_result.results)
        trace_events.append(
            TraceEvent(
                event_type="tool_result",
                tool_name=tool_result.tool_name,
                status="error" if tool_result.error else "ok",
                summary=f"result_count={len(tool_result.results)}",
            )
        )
        if tool_result.audit_summary:
            trace_events.append(
                TraceEvent(
                    event_type="retrieval_channels_summarized",
                    tool_name=tool_result.tool_name,
                    status="ok",
                    summary=_format_audit_summary(tool_result.audit_summary),
                )
            )

        if tool_result.error:
            answer = f"已尝试使用 hybrid repo RAG 检索 `{decision.keyword}`，但工具调用失败。"
        elif related_files:
            citations = _format_citations(tool_result.results)
            answer = (
                f"已基于 hybrid repo RAG 检索 `{decision.keyword}`，"
                f"找到相关证据：{citations}。"
            )
        else:
            answer = f"已基于 hybrid repo RAG 检索 `{decision.keyword}`，没有找到相关证据。"

        return AgentLoopResult(
            answer=answer,
            related_files=related_files,
            tool_calls=[tool_result.call_summary()],
            trace_events_internal=trace_events,
        )

    def _run_repo_rag(
        self,
        *,
        repo_path: str,
        keyword: str,
        search_plan: SearchPlan,
    ):
        return self.tool_executor.search_repo_rag(
            repo_path=repo_path,
            keyword=keyword,
            search_plan=search_plan,
        )


def _extract_search_keyword(message: str) -> str | None:
    tokens = TOKEN_PATTERN.findall(message)
    for token in tokens:
        if (
            "_" in token
            or "." in token
            or token.endswith("Error")
            or token[:1].isupper()
        ):
            return token
    return None


def _should_record_query_understanding(search_plan: SearchPlan) -> bool:
    return bool(search_plan.path_hints or len(search_plan.symbols) > 1)


def _asks_about_unimplemented_vector_stack(message: str) -> bool:
    lower = message.lower()
    has_capability_term = any(
        term in lower
        for term in (
            "embedding",
            "milvus",
            "elasticsearch",
            "pgvector",
            "qdrant",
            "memory",
            "vector",
        )
    )
    if not has_capability_term:
        return False
    if any(term in message for term in ("哪里", "在哪", "哪个文件", "定位")) or any(
        term in lower for term in ("where", "locate", "find")
    ):
        return False
    return any(
        term in message
        for term in (
            "实现了吗",
            "实现了么",
            "有没有",
            "是否",
            "当前",
            "支持",
            "接入",
            "上了",
            "弄了吗",
            "弄了么",
            "做了吗",
            "做了么",
            "了吗",
            "了么",
        )
    )


def _unique_related_files(results: list[dict[str, str | int]]) -> list[str]:
    related_files: list[str] = []
    seen: set[str] = set()

    for result in results:
        file_path = result.get("file_path")
        if not isinstance(file_path, str):
            continue
        if _is_absolute_path(file_path):
            continue
        if file_path in seen:
            continue
        related_files.append(file_path)
        seen.add(file_path)

    return related_files


def _format_citations(results: list[dict[str, str | int]]) -> str:
    citations: list[str] = []
    for result in results:
        file_path = result.get("file_path")
        start_line = result.get("start_line", result.get("line_number"))
        end_line = result.get("end_line", start_line)
        if not isinstance(file_path, str):
            continue
        citations.append(f"{file_path}:{start_line}-{end_line}")
    return ", ".join(citations)


def _format_audit_summary(audit_summary: dict[str, str | int | float]) -> str:
    return "; ".join(f"{key}={value}" for key, value in audit_summary.items())


def _is_absolute_path(file_path: str) -> bool:
    return PureWindowsPath(file_path).is_absolute() or PurePosixPath(
        file_path
    ).is_absolute()
