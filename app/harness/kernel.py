from dataclasses import dataclass, field
import re

from app.tools.tool_executor import ToolExecutor


TOKEN_PATTERN = re.compile(r"[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z0-9_]+)*")
ALLOWED_TOOL_RISK = "low"


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

    def is_allowed(self, name: str) -> bool:
        return self.rejection_reason(name) is None

    def rejection_reason(self, name: str) -> str | None:
        spec = self.get(name)
        if spec is None:
            return "not_registered"
        if not spec.read_only:
            return "not_read_only"
        if spec.risk != ALLOWED_TOOL_RISK:
            return "risk_not_allowed"
        return None


class AgentLoop:
    def __init__(
        self,
        *,
        router: RequestRouter | None = None,
        tool_registry: ToolRegistry | None = None,
        tool_executor: ToolExecutor | None = None,
    ) -> None:
        self.router = router or RequestRouter()
        self.tool_registry = tool_registry or ToolRegistry.with_default_tools()
        self.tool_executor = tool_executor or ToolExecutor()

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
                answer="未提取到可搜索关键词，因此没有调用仓库工具。",
                trace_events_internal=trace_events,
            )

        rejection_reason = self.tool_registry.rejection_reason("search_code")
        if rejection_reason:
            return AgentLoopResult(
                answer="仓库搜索工具未通过 registry 校验，因此没有调用仓库工具。",
                trace_events_internal=[
                    *trace_events,
                    TraceEvent(
                        event_type="tool_rejected",
                        tool_name="search_code",
                        status="error",
                        summary=(
                            "tool=search_code rejected by registry gate; "
                            f"reason={rejection_reason}"
                        ),
                    ),
                ],
            )

        trace_events.append(
            TraceEvent(
                event_type="tool_call",
                tool_name="search_code",
                status="ok",
                summary=f"tool=search_code; keyword={decision.keyword}",
            )
        )
        tool_result = self.tool_executor.search_code(
            repo_path=request.repo_path,
            keyword=decision.keyword,
        )
        related_files = _unique_related_files(tool_result.results)
        trace_events.append(
            TraceEvent(
                event_type="tool_result",
                tool_name="search_code",
                status="error" if tool_result.error else "ok",
                summary=f"result_count={len(tool_result.results)}",
            )
        )

        if tool_result.error:
            answer = f"已尝试使用只读仓库工具搜索 `{decision.keyword}`，但工具调用失败。"
        elif related_files:
            answer = f"已使用只读仓库工具搜索 `{decision.keyword}`，找到相关文件。"
        else:
            answer = f"已使用只读仓库工具搜索 `{decision.keyword}`，没有找到相关文件。"

        return AgentLoopResult(
            answer=answer,
            related_files=related_files,
            tool_calls=[tool_result.call_summary()],
            trace_events_internal=trace_events,
        )


def _extract_search_keyword(message: str) -> str | None:
    tokens = TOKEN_PATTERN.findall(message)
    for token in tokens:
        if "_" in token or "." in token or token.endswith("Error"):
            return token
    return None


def _unique_related_files(results: list[dict[str, str | int]]) -> list[str]:
    related_files: list[str] = []
    seen: set[str] = set()

    for result in results:
        file_path = result.get("file_path")
        if not isinstance(file_path, str):
            continue
        if file_path in seen:
            continue
        related_files.append(file_path)
        seen.add(file_path)

    return related_files
