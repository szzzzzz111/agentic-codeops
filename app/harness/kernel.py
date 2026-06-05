from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath, PureWindowsPath
import re

from app.audit.manager import (
    AuditManager,
    build_event_from_trace,
    build_trace_event,
    format_recovery_answer,
    is_audit_recovery_request,
    recovery_query,
)
from app.answering.grounded_answer import GroundedAnswerGenerator
from app.assistant.control_surface import AssistantControlSurface, is_assistant_status_request
from app.longtask.manager import LongTaskManager
from app.longtask.planner import LongTaskPlanner
from app.memory.manager import MemoryManager
from app.patching.manager import PatchManager
from app.patching.parser import parse_patch_verify_confirmation
from app.patching.types import ToolInvocationContext
from app.providers.model_provider import ModelProvider, load_model_provider_from_env
from app.rag.query_understanding import QueryUnderstanding, SearchPlan
from app.rag.repo_rag import HybridRepoRetriever
from app.tools.tool_executor import ToolExecutionResult, ToolExecutor
from app.verification.runner import (
    command_argv,
    format_verification_answer,
    parse_verification_request,
    unsupported_verification_answer,
)


TOKEN_PATTERN = re.compile(r"[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z0-9_]+)*")
ALLOWED_TOOL_RISK = "low"
REPO_RAG_TOOL = "repo_rag"
PATCH_APPLY_TOOL = "patch_apply"
VERIFICATION_RUN_TOOL = "verification_run"
_ROUTING_STOPWORDS = {
    "hello",
    "hi",
    "hey",
    "can",
    "could",
    "would",
    "should",
    "please",
    "thanks",
    "thank",
    "does",
    "do",
    "is",
    "are",
    "what",
    "why",
    "how",
}
DENY_ANSWER = "仓库工具未通过权限策略校验，因此本次没有执行仓库工具。"
ASK_ANSWER = "工具调用需要人工审批，因此本次没有执行仓库工具。"
NO_TOOL_ANSWER = "未提取到可搜索关键词，因此没有调用仓库工具。"
CAPABILITY_STATUS_KEYWORD = "capability_status"
V11_CAPABILITY_STATUS_ANSWER = (
    "V11 提供 Grounded Answer 和 Model Provider Boundary；"
    "默认 fake provider 保持离线可验证，显式配置后可使用 OpenAI-compatible provider；"
    "当前未实现 query rewrite、rerank、memory 或 context compression。"
)
V12_CAPABILITY_STATUS_ANSWER = (
    "V12 提供 deterministic query rewrite 和 rerank；"
    "默认不启用真实 LLM rewrite/rerank；"
    "当前未实现 memory 或 context compression。"
)
V13_CAPABILITY_STATUS_ANSWER = (
    "V13 提供 SQLite-backed PREF/LTM 和进程内 STM；"
    "支持明确 memory 指令和内部 memory audit；"
    "当前未实现向量记忆、自动模型总结、跨 repo 智能召回或 context compression。"
)
VECTOR_CAPABILITY_STATUS_ANSWER = (
    "V9 提供轻量 embedding retrieval 和 hybrid search；"
    "当前未默认接入 Milvus、Elasticsearch、PgVector、Qdrant 或真实外部 embedding 服务。"
)
V16_CAPABILITY_STATUS_ANSWER = (
    "V16 提供 Safe Patch Authoring：可基于仓库证据生成 patch proposal，"
    "并在明确确认后受控 apply；V17 提供独立 Verification Runner；"
    "V18 提供明确组合确认下的 Patch + Verify Loop；"
    "当前未实现 Persistent Audit / Recovery 或 Worktree Isolation。"
)


@dataclass(frozen=True)
class AgentLoopRequest:
    message: str
    repo_path: str
    trace_id: str
    user_id: str = ""
    session_id: str = ""


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


@dataclass(frozen=True)
class _PatchLoopApplyResult:
    completed: object
    tool_result: ToolExecutionResult
    trace_events: list[TraceEvent]


@dataclass(frozen=True)
class _PatchLoopVerificationResult:
    answer: str
    tool_result: ToolExecutionResult
    trace_events: list[TraceEvent]


class RequestRouter:
    def route(self, message: str) -> RouteDecision:
        if _asks_about_unimplemented_vector_stack(message):
            return RouteDecision(
                route="capability_status",
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
                    name=REPO_RAG_TOOL,
                    description="Search a repository using read-only repo-local RAG.",
                    read_only=True,
                    risk=ALLOWED_TOOL_RISK,
                ),
                ToolSpec(
                    name=PATCH_APPLY_TOOL,
                    description="Apply a confirmed repository patch.",
                    read_only=False,
                    risk="write",
                    requires_approval=True,
                ),
                ToolSpec(
                    name=VERIFICATION_RUN_TOOL,
                    description="Run a whitelisted repository verification command.",
                    read_only=False,
                    risk="write",
                    requires_approval=True,
                ),
            ]
        )

    def get(self, name: str) -> ToolSpec | None:
        return self._specs.get(name)


class PermissionPolicy:
    def decide(
        self,
        tool_spec: ToolSpec | None,
        tool_name: str = REPO_RAG_TOOL,
        context: ToolInvocationContext | None = None,
    ) -> PermissionDecision:
        if tool_spec is None:
            return PermissionDecision(
                tool_name=tool_name,
                status="deny",
                reason="not_registered",
            )
        if tool_spec.name == PATCH_APPLY_TOOL:
            return _decide_patch_apply(tool_spec, context)
        if tool_spec.name == VERIFICATION_RUN_TOOL:
            return _decide_verification_run(tool_spec, context)
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
    def evaluate(
        self,
        decision: PermissionDecision,
        context: ToolInvocationContext | None = None,
    ) -> bool:
        if decision.tool_name == PATCH_APPLY_TOOL and decision.status == "ask":
            return _valid_patch_context(context)
        if decision.tool_name == VERIFICATION_RUN_TOOL and decision.status == "ask":
            return _valid_verification_context(context)
        return decision.status == "allow"


def _decide_patch_apply(
    tool_spec: ToolSpec,
    context: ToolInvocationContext | None,
) -> PermissionDecision:
    if not _valid_patch_context(context):
        return PermissionDecision(
            tool_name=tool_spec.name,
            status="deny",
            reason=_patch_context_rejection_reason(context),
        )
    return PermissionDecision(
        tool_name=tool_spec.name,
        status="ask",
        reason="approval_required",
    )


def _valid_patch_context(context: ToolInvocationContext | None) -> bool:
    return bool(
        context is not None
        and context.tool_name == PATCH_APPLY_TOOL
        and context.intent == "patch_apply"
        and context.confirmed
        and context.patch_status == "pending"
        and context.diff_hash_match
        and context.expires_at_valid
        and context.scope_valid
    )


def _patch_context_rejection_reason(context: ToolInvocationContext | None) -> str:
    if context is None or not context.confirmed:
        return "missing_confirmation"
    if context.patch_status != "pending":
        return "patch_not_pending"
    if not context.diff_hash_match:
        return "patch_hash_mismatch"
    if not context.expires_at_valid:
        return "patch_expired"
    if not context.scope_valid:
        return "patch_scope_invalid"
    return "patch_context_invalid"


def _decide_verification_run(
    tool_spec: ToolSpec,
    context: ToolInvocationContext | None,
) -> PermissionDecision:
    if not _valid_verification_context(context):
        return PermissionDecision(
            tool_name=tool_spec.name,
            status="deny",
            reason=_verification_context_rejection_reason(context),
        )
    return PermissionDecision(
        tool_name=tool_spec.name,
        status="ask",
        reason="approval_required",
    )


def _valid_verification_context(context: ToolInvocationContext | None) -> bool:
    return bool(
        context is not None
        and context.tool_name == VERIFICATION_RUN_TOOL
        and context.intent == "verification_run"
        and context.confirmed
        and context.scope_valid
        and command_argv(context.command_label) is not None
    )


def _verification_context_rejection_reason(
    context: ToolInvocationContext | None,
) -> str:
    if context is None or not context.confirmed:
        return "missing_confirmation"
    if not context.scope_valid:
        return "verification_scope_invalid"
    if command_argv(context.command_label) is None:
        return "verification_command_not_whitelisted"
    return "verification_context_invalid"


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
        model_provider: ModelProvider | None = None,
        memory_manager: MemoryManager | None = None,
        long_task_manager: LongTaskManager | None = None,
        assistant_control_surface: AssistantControlSurface | None = None,
        patch_manager: PatchManager | None = None,
        audit_manager: AuditManager | None = None,
    ) -> None:
        self.router = router or RequestRouter()
        self.tool_registry = tool_registry or ToolRegistry.with_default_tools()
        self.tool_executor = tool_executor or ToolExecutor(repo_retriever=repo_retriever)
        self.permission_policy = permission_policy or PermissionPolicy()
        self.approval_gate = approval_gate or ApprovalGate()
        self.query_understanding = query_understanding or QueryUnderstanding()
        self.memory_manager = memory_manager or MemoryManager()
        provider = model_provider or load_model_provider_from_env()
        self.long_task_manager = long_task_manager or LongTaskManager(
            planner=LongTaskPlanner(
                provider=provider,
                provider_enabled=_is_real_provider(provider),
            )
        )
        self.assistant_control_surface = assistant_control_surface or (
            AssistantControlSurface(
                memory_manager=self.memory_manager,
                long_task_manager=self.long_task_manager,
            )
        )
        self.patch_manager = patch_manager or PatchManager()
        self.audit_manager = audit_manager or AuditManager()
        self.grounded_answer = GroundedAnswerGenerator(provider=provider)

    def run(self, request: AgentLoopRequest) -> AgentLoopResult:
        result = self._run_inner(request)
        return self._record_audit_and_return(request, result)

    def _run_inner(self, request: AgentLoopRequest) -> AgentLoopResult:
        memory_command = self.memory_manager.handle_command(
            user_id=request.user_id,
            session_id=request.session_id,
            repo_path=request.repo_path,
            message=request.message,
        )
        if memory_command.handled:
            return AgentLoopResult(
                answer=memory_command.answer,
                trace_events_internal=[
                    TraceEvent(
                        event_type="memory_command",
                        status="ok"
                        if "unavailable" not in memory_command.audit_summary
                        else "error",
                        summary=memory_command.audit_summary,
                    ),
                ],
            )

        long_task_command = self.long_task_manager.handle_command(
            user_id=request.user_id,
            session_id=request.session_id,
            repo_path=request.repo_path,
            message=request.message,
        )
        if long_task_command.handled:
            trace_events = [
                TraceEvent(
                    event_type="long_task_command",
                    status="ok"
                    if "unavailable" not in long_task_command.audit_summary
                    else "error",
                    summary=long_task_command.audit_summary,
                )
            ]
            if long_task_command.tool_action != REPO_RAG_TOOL:
                return AgentLoopResult(
                    answer=long_task_command.answer,
                    trace_events_internal=trace_events,
                )
            return self._run_long_task_tool_action(
                request=request,
                command=long_task_command,
                trace_events=trace_events,
            )

        if is_assistant_status_request(request.message):
            answer = self.assistant_control_surface.answer_status(
                user_id=request.user_id,
                session_id=request.session_id,
                repo_path=request.repo_path,
            )
            return AgentLoopResult(
                answer=answer,
                trace_events_internal=[
                    TraceEvent(
                        event_type="assistant_control_surface",
                        status="ok" if "状态不可用" not in answer else "error",
                        summary="assistant_status=returned",
                    )
                ],
            )

        patch_verify_confirmation = parse_patch_verify_confirmation(request.message)
        if patch_verify_confirmation.handled:
            return self._run_patch_verify_loop(
                request=request,
                patch_id=patch_verify_confirmation.patch_id,
                command_label=patch_verify_confirmation.command_label,
                rejected=patch_verify_confirmation.rejected,
                reason=patch_verify_confirmation.reason,
            )

        patch_confirmation = self.patch_manager.prepare_apply(
            user_id=request.user_id,
            repo_path=request.repo_path,
            message=request.message,
        )
        if patch_confirmation.handled:
            if patch_confirmation.context is None or not patch_confirmation.diff_text:
                return AgentLoopResult(
                    answer=patch_confirmation.answer,
                    trace_events_internal=[
                        TraceEvent(
                            event_type="patch_command",
                            status="error",
                            summary=patch_confirmation.audit_summary,
                        )
                    ],
                )
            return self._run_patch_apply(
                request=request,
                command=patch_confirmation,
            )

        if self.patch_manager.is_patch_proposal_request(request.message):
            return self._run_patch_proposal(request)

        verification_request = parse_verification_request(request.message)
        if verification_request.handled:
            if verification_request.rejected or not verification_request.command_label:
                return AgentLoopResult(
                    answer=unsupported_verification_answer(),
                    trace_events_internal=[
                        TraceEvent(
                            event_type="verification_command",
                            status="error",
                            summary=f"reason={verification_request.reason}",
                        )
                    ],
                )
            return self._run_verification(
                request=request,
                command_label=verification_request.command_label,
            )

        if is_audit_recovery_request(request.message):
            return self._run_audit_recovery(request)

        decision = self.router.route(request.message)
        trace_events = [
            TraceEvent(
                event_type="request_routed",
                status="ok",
                summary=f"route={decision.route}; reason={decision.reason}",
            )
        ]

        if decision.route == "capability_status":
            return AgentLoopResult(
                answer=_capability_status_answer(request.message),
                trace_events_internal=trace_events,
            )

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

        tool_spec = self.tool_registry.get(REPO_RAG_TOOL)
        permission_decision = self.permission_policy.decide(
            tool_spec,
            tool_name=REPO_RAG_TOOL,
        )
        trace_events.append(
            TraceEvent(
                event_type="permission_checked",
                tool_name=REPO_RAG_TOOL,
                status="ok" if permission_decision.status == "allow" else "error",
                summary=(
                    f"tool={REPO_RAG_TOOL}; "
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
                        tool_name=REPO_RAG_TOOL,
                        status="error",
                        summary=(
                            f"tool={REPO_RAG_TOOL} rejected by permission policy; "
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
                        tool_name=REPO_RAG_TOOL,
                        status="ok",
                        summary=f"tool={REPO_RAG_TOOL} requires approval",
                    ),
                ],
            )

        memory_summary = self.memory_manager.summarize_for_request(
            user_id=request.user_id,
            session_id=request.session_id,
            repo_path=request.repo_path,
        )
        trace_events.append(
            TraceEvent(
                event_type="memory_summarized",
                status="ok" if "unavailable" not in memory_summary else "error",
                summary=memory_summary,
            )
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
        channel_summary = _channel_audit_summary(tool_result.audit_summary)
        rewrite_summary = _prefixed_audit_summary(
            tool_result.audit_summary,
            "rewrite_",
        )
        rerank_summary = _prefixed_audit_summary(
            tool_result.audit_summary,
            "rerank_",
        )
        if rewrite_summary:
            trace_events.append(
                TraceEvent(
                    event_type="query_rewrite_summarized",
                    tool_name=tool_result.tool_name,
                    status="ok"
                    if rewrite_summary.get("rewrite_status") == "success"
                    else "error",
                    summary=_format_audit_summary(rewrite_summary),
                )
            )
        if rerank_summary:
            trace_events.append(
                TraceEvent(
                    event_type="rerank_summarized",
                    tool_name=tool_result.tool_name,
                    status="ok"
                    if rerank_summary.get("rerank_status") == "success"
                    else "error",
                    summary=_format_audit_summary(rerank_summary),
                )
            )
        if channel_summary:
            trace_events.append(
                TraceEvent(
                    event_type="retrieval_channels_summarized",
                    tool_name=tool_result.tool_name,
                    status="ok",
                    summary=_format_audit_summary(channel_summary),
                )
            )
        if tool_result.evidence_pack is not None:
            trace_events.append(
                TraceEvent(
                    event_type="evidence_pack_summarized",
                    tool_name=tool_result.tool_name,
                    status="ok",
                    summary=_format_audit_summary(
                        tool_result.evidence_pack.audit_summary()
                    ),
                )
            )

        if tool_result.error:
            answer = f"已尝试使用 hybrid repo RAG 检索 `{decision.keyword}`，但工具调用失败。"
        elif tool_result.evidence_pack is not None:
            grounded_result = self.grounded_answer.generate(tool_result.evidence_pack)
            trace_events.append(
                TraceEvent(
                    event_type="model_provider_summarized",
                    status="ok"
                    if grounded_result.audit_summary.get("status") == "success"
                    else "error",
                    summary=_format_audit_summary(grounded_result.audit_summary),
                )
            )
            answer = grounded_result.answer
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

    def _run_long_task_tool_action(
        self,
        *,
        request: AgentLoopRequest,
        command,
        trace_events: list[TraceEvent],
    ) -> AgentLoopResult:
        tool_spec = self.tool_registry.get(REPO_RAG_TOOL)
        permission_decision = self.permission_policy.decide(
            tool_spec,
            tool_name=REPO_RAG_TOOL,
        )
        trace_events.append(
            TraceEvent(
                event_type="permission_checked",
                tool_name=REPO_RAG_TOOL,
                status="ok" if permission_decision.status == "allow" else "error",
                summary=(
                    f"tool={REPO_RAG_TOOL}; "
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
                        tool_name=REPO_RAG_TOOL,
                        status="error",
                        summary=(
                            f"tool={REPO_RAG_TOOL} rejected by permission policy; "
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
                        tool_name=REPO_RAG_TOOL,
                        status="ok",
                        summary=f"tool={REPO_RAG_TOOL} requires approval",
                    ),
                ],
            )

        search_plan = self.query_understanding.build_search_plan(command.query_text)
        trace_events.append(
            TraceEvent(
                event_type="tool_call",
                tool_name=REPO_RAG_TOOL,
                status="ok",
                summary=f"tool={REPO_RAG_TOOL}; keyword={command.query_text}",
            )
        )
        tool_result = self._run_repo_rag(
            repo_path=request.repo_path,
            keyword=command.query_text,
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
        completed = self.long_task_manager.complete_tool_action(
            repo_path=request.repo_path,
            user_id=request.user_id,
            task_id=command.task_id or "",
            results=tool_result.results,
            error=tool_result.error,
        )
        trace_events.append(
            TraceEvent(
                event_type="long_task_step_summarized",
                tool_name=REPO_RAG_TOOL,
                status="ok" if tool_result.error is None else "error",
                summary=completed.audit_summary,
            )
        )
        return AgentLoopResult(
            answer=completed.answer,
            related_files=related_files,
            tool_calls=[tool_result.call_summary()],
            trace_events_internal=trace_events,
        )

    def _run_patch_proposal(self, request: AgentLoopRequest) -> AgentLoopResult:
        search_plan = self.query_understanding.build_search_plan(request.message)
        keyword = search_plan.keywords[0] if search_plan.keywords else request.message
        trace_events = [
            TraceEvent(
                event_type="patch_command",
                status="ok",
                summary="patch_intent=proposal",
            )
        ]
        tool_spec = self.tool_registry.get(REPO_RAG_TOOL)
        permission_decision = self.permission_policy.decide(
            tool_spec,
            tool_name=REPO_RAG_TOOL,
        )
        trace_events.append(
            TraceEvent(
                event_type="permission_checked",
                tool_name=REPO_RAG_TOOL,
                status="ok" if permission_decision.status == "allow" else "error",
                summary=(
                    f"tool={REPO_RAG_TOOL}; "
                    f"decision={permission_decision.status}; "
                    f"reason={permission_decision.reason}"
                ),
            )
        )
        if permission_decision.status == "deny":
            return AgentLoopResult(answer=DENY_ANSWER, trace_events_internal=trace_events)
        if not self.approval_gate.evaluate(permission_decision):
            return AgentLoopResult(answer=ASK_ANSWER, trace_events_internal=trace_events)

        tool_result = self._run_repo_rag(
            repo_path=request.repo_path,
            keyword=keyword,
            search_plan=search_plan,
        )
        related_files = _unique_related_files(tool_result.results)
        patch_result = self.patch_manager.propose_patch(
            user_id=request.user_id,
            repo_path=request.repo_path,
            message=request.message,
            evidence_pack=tool_result.evidence_pack,
        )
        trace_events.append(
            TraceEvent(
                event_type="patch_proposal_summarized",
                status="ok" if patch_result.patch_id else "error",
                summary=patch_result.audit_summary,
            )
        )
        return AgentLoopResult(
            answer=patch_result.answer,
            related_files=related_files,
            tool_calls=[tool_result.call_summary()],
            trace_events_internal=trace_events,
        )

    def _run_patch_apply(
        self,
        *,
        request: AgentLoopRequest,
        command,
    ) -> AgentLoopResult:
        context = command.context
        tool_spec = self.tool_registry.get(PATCH_APPLY_TOOL)
        permission_decision = self.permission_policy.decide(
            tool_spec,
            tool_name=PATCH_APPLY_TOOL,
            context=context,
        )
        trace_events = [
            TraceEvent(
                event_type="patch_command",
                status="ok",
                summary=command.audit_summary,
            ),
            TraceEvent(
                event_type="permission_checked",
                tool_name=PATCH_APPLY_TOOL,
                status="ok" if permission_decision.status == "ask" else "error",
                summary=(
                    f"tool={PATCH_APPLY_TOOL}; "
                    f"decision={permission_decision.status}; "
                    f"reason={permission_decision.reason}"
                ),
            ),
        ]
        if permission_decision.status == "deny":
            return AgentLoopResult(
                answer=DENY_ANSWER,
                trace_events_internal=[
                    *trace_events,
                    TraceEvent(
                        event_type="tool_rejected",
                        tool_name=PATCH_APPLY_TOOL,
                        status="error",
                        summary=f"reason={permission_decision.reason}",
                    ),
                ],
            )
        if not self.approval_gate.evaluate(permission_decision, context=context):
            return AgentLoopResult(
                answer=ASK_ANSWER,
                trace_events_internal=[
                    *trace_events,
                    TraceEvent(
                        event_type="approval_required",
                        tool_name=PATCH_APPLY_TOOL,
                    ),
                ],
            )
        tool_result = self.tool_executor.patch_apply(
            repo_path=request.repo_path,
            diff_text=command.diff_text,
        )
        trace_events.append(
            TraceEvent(
                event_type="tool_result",
                tool_name=PATCH_APPLY_TOOL,
                status="error" if tool_result.error else "ok",
                summary=f"result_count={len(tool_result.results)}",
            )
        )
        apply_result = getattr(tool_result, "patch_apply_result", None)
        completed = self.patch_manager.complete_apply(
            repo_path=request.repo_path,
            user_id=request.user_id,
            patch_id=command.patch_id or "",
            result=apply_result,
        )
        return AgentLoopResult(
            answer=completed.answer,
            tool_calls=[tool_result.call_summary()],
            trace_events_internal=[
                *trace_events,
                TraceEvent(
                    event_type="patch_apply_summarized",
                    tool_name=PATCH_APPLY_TOOL,
                    status="ok" if tool_result.error is None else "error",
                    summary=completed.audit_summary,
                ),
            ],
        )

    def _run_patch_verify_loop(
        self,
        *,
        request: AgentLoopRequest,
        patch_id: str,
        command_label: str,
        rejected: bool,
        reason: str,
    ) -> AgentLoopResult:
        trace_events = [
            TraceEvent(
                event_type="patch_verify_loop_started",
                status="error" if rejected else "ok",
                summary=(
                    f"patch_id={patch_id}; command_label={command_label}; "
                    f"reason={reason}"
                ),
            )
        ]
        if rejected or not patch_id or not command_label:
            return AgentLoopResult(
                answer=unsupported_verification_answer(),
                trace_events_internal=trace_events,
            )

        patch_command = self.patch_manager.prepare_apply(
            user_id=request.user_id,
            repo_path=request.repo_path,
            message=f"确认 patch {patch_id}",
        )
        if patch_command.context is None or not patch_command.diff_text:
            return AgentLoopResult(
                answer=patch_command.answer,
                trace_events_internal=[
                    *trace_events,
                    TraceEvent(
                        event_type="patch_command",
                        status="error",
                        summary=patch_command.audit_summary,
                    ),
                ],
            )

        patch_result = self._apply_patch_for_loop(
            request=request,
            command=patch_command,
            trace_events=trace_events,
        )
        apply_result = getattr(patch_result.tool_result, "patch_apply_result", None)
        if patch_result.tool_result.error or apply_result is None or not apply_result.applied:
            failed_answer = getattr(patch_result.completed, "answer", "") or DENY_ANSWER
            return AgentLoopResult(
                answer=failed_answer,
                tool_calls=[patch_result.tool_result.call_summary()],
                trace_events_internal=patch_result.trace_events,
            )

        verification_result = self._verify_after_patch_apply(
            request=request,
            command_label=command_label,
            trace_events=patch_result.trace_events,
        )
        return AgentLoopResult(
            answer=_format_patch_verify_answer(
                patch_result.completed.answer,
                verification_result.answer,
                verification_result.tool_result.audit_summary,
            ),
            tool_calls=[
                patch_result.tool_result.call_summary(),
                verification_result.tool_result.call_summary(),
            ],
            trace_events_internal=verification_result.trace_events,
        )

    def _apply_patch_for_loop(
        self,
        *,
        request: AgentLoopRequest,
        command,
        trace_events: list[TraceEvent],
    ):
        context = command.context
        tool_spec = self.tool_registry.get(PATCH_APPLY_TOOL)
        permission_decision = self.permission_policy.decide(
            tool_spec,
            tool_name=PATCH_APPLY_TOOL,
            context=context,
        )
        next_events = [
            *trace_events,
            TraceEvent(
                event_type="patch_command",
                status="ok",
                summary=command.audit_summary,
            ),
            TraceEvent(
                event_type="permission_checked",
                tool_name=PATCH_APPLY_TOOL,
                status="ok" if permission_decision.status == "ask" else "error",
                summary=(
                    f"tool={PATCH_APPLY_TOOL}; "
                    f"decision={permission_decision.status}; "
                    f"reason={permission_decision.reason}"
                ),
            ),
        ]
        if permission_decision.status == "deny" or not self.approval_gate.evaluate(
            permission_decision,
            context=context,
        ):
            tool_result = ToolExecutionResult(
                tool_name=PATCH_APPLY_TOOL,
                parameters={},
                error=permission_decision.reason,
            )
            return _PatchLoopApplyResult(
                completed=command,
                tool_result=tool_result,
                trace_events=[
                    *next_events,
                    TraceEvent(
                        event_type="tool_rejected",
                        tool_name=PATCH_APPLY_TOOL,
                        status="error",
                        summary=f"reason={permission_decision.reason}",
                    ),
                ],
            )

        tool_result = self.tool_executor.patch_apply(
            repo_path=request.repo_path,
            diff_text=command.diff_text,
        )
        apply_result = getattr(tool_result, "patch_apply_result", None)
        completed = self.patch_manager.complete_apply(
            repo_path=request.repo_path,
            user_id=request.user_id,
            patch_id=command.patch_id or "",
            result=apply_result,
        )
        status = "ok" if tool_result.error is None else "error"
        return _PatchLoopApplyResult(
            completed=completed,
            tool_result=tool_result,
            trace_events=[
                *next_events,
                TraceEvent(
                    event_type="tool_result",
                    tool_name=PATCH_APPLY_TOOL,
                    status=status,
                    summary=f"result_count={len(tool_result.results)}",
                ),
                TraceEvent(
                    event_type="patch_apply_summarized",
                    tool_name=PATCH_APPLY_TOOL,
                    status=status,
                    summary=completed.audit_summary,
                ),
                TraceEvent(
                    event_type="patch_verify_apply_summarized",
                    tool_name=PATCH_APPLY_TOOL,
                    status=status,
                    summary=completed.audit_summary,
                ),
            ],
        )

    def _verify_after_patch_apply(
        self,
        *,
        request: AgentLoopRequest,
        command_label: str,
        trace_events: list[TraceEvent],
    ):
        context = ToolInvocationContext(
            tool_name=VERIFICATION_RUN_TOOL,
            user_id=request.user_id,
            intent="verification_run",
            command_label=command_label,
            confirmed=True,
            scope_valid=_valid_repo_scope(request.repo_path),
        )
        tool_spec = self.tool_registry.get(VERIFICATION_RUN_TOOL)
        permission_decision = self.permission_policy.decide(
            tool_spec,
            tool_name=VERIFICATION_RUN_TOOL,
            context=context,
        )
        next_events = [
            *trace_events,
            TraceEvent(
                event_type="permission_checked",
                tool_name=VERIFICATION_RUN_TOOL,
                status="ok" if permission_decision.status == "ask" else "error",
                summary=(
                    f"tool={VERIFICATION_RUN_TOOL}; "
                    f"decision={permission_decision.status}; "
                    f"reason={permission_decision.reason}"
                ),
            ),
        ]
        if permission_decision.status == "deny" or not self.approval_gate.evaluate(
            permission_decision,
            context=context,
        ):
            tool_result = ToolExecutionResult(
                tool_name=VERIFICATION_RUN_TOOL,
                parameters={"command_label": command_label},
                error=permission_decision.reason,
            )
            return _PatchLoopVerificationResult(
                answer=DENY_ANSWER,
                tool_result=tool_result,
                trace_events=[
                    *next_events,
                    TraceEvent(
                        event_type="tool_rejected",
                        tool_name=VERIFICATION_RUN_TOOL,
                        status="error",
                        summary=f"reason={permission_decision.reason}",
                    ),
                ],
            )

        tool_result = self.tool_executor.verification_run(
            repo_path=request.repo_path,
            command_label=command_label,
        )
        answer = _verification_answer_from_tool_result(tool_result)
        status = (
            "error"
            if tool_result.audit_summary.get("status") not in {"success", ""}
            else "ok"
        )
        return _PatchLoopVerificationResult(
            answer=answer,
            tool_result=tool_result,
            trace_events=[
                *next_events,
                TraceEvent(
                    event_type="tool_result",
                    tool_name=VERIFICATION_RUN_TOOL,
                    status="error" if tool_result.error else "ok",
                    summary=f"status={tool_result.audit_summary.get('status', '')}",
                ),
                TraceEvent(
                    event_type="patch_verify_verification_summarized",
                    tool_name=VERIFICATION_RUN_TOOL,
                    status=status,
                    summary=_verification_trace_summary(tool_result.audit_summary),
                ),
            ],
        )

    def _run_verification(
        self,
        *,
        request: AgentLoopRequest,
        command_label: str,
    ) -> AgentLoopResult:
        context = ToolInvocationContext(
            tool_name=VERIFICATION_RUN_TOOL,
            user_id=request.user_id,
            intent="verification_run",
            command_label=command_label,
            confirmed=True,
            scope_valid=_valid_repo_scope(request.repo_path),
        )
        tool_spec = self.tool_registry.get(VERIFICATION_RUN_TOOL)
        permission_decision = self.permission_policy.decide(
            tool_spec,
            tool_name=VERIFICATION_RUN_TOOL,
            context=context,
        )
        trace_events = [
            TraceEvent(
                event_type="verification_command",
                status="ok",
                summary=f"command_label={command_label}",
            ),
            TraceEvent(
                event_type="permission_checked",
                tool_name=VERIFICATION_RUN_TOOL,
                status="ok" if permission_decision.status == "ask" else "error",
                summary=(
                    f"tool={VERIFICATION_RUN_TOOL}; "
                    f"decision={permission_decision.status}; "
                    f"reason={permission_decision.reason}"
                ),
            ),
        ]
        if permission_decision.status == "deny":
            return AgentLoopResult(
                answer=DENY_ANSWER,
                trace_events_internal=[
                    *trace_events,
                    TraceEvent(
                        event_type="tool_rejected",
                        tool_name=VERIFICATION_RUN_TOOL,
                        status="error",
                        summary=f"reason={permission_decision.reason}",
                    ),
                ],
            )
        if not self.approval_gate.evaluate(permission_decision, context=context):
            return AgentLoopResult(
                answer=ASK_ANSWER,
                trace_events_internal=[
                    *trace_events,
                    TraceEvent(
                        event_type="approval_required",
                        tool_name=VERIFICATION_RUN_TOOL,
                    ),
                ],
            )
        tool_result = self.tool_executor.verification_run(
            repo_path=request.repo_path,
            command_label=command_label,
        )
        trace_events.append(
            TraceEvent(
                event_type="tool_result",
                tool_name=VERIFICATION_RUN_TOOL,
                status="error" if tool_result.error else "ok",
                summary=f"status={tool_result.audit_summary.get('status', '')}",
            )
        )
        trace_events.append(
            TraceEvent(
                event_type="verification_summarized",
                tool_name=VERIFICATION_RUN_TOOL,
                status="error"
                if tool_result.audit_summary.get("status") not in {"success", ""}
                else "ok",
                summary=_verification_trace_summary(tool_result.audit_summary),
            )
        )
        return AgentLoopResult(
            answer=_verification_answer_from_tool_result(tool_result),
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

    def _run_audit_recovery(self, request: AgentLoopRequest) -> AgentLoopResult:
        query_type, identifier = recovery_query(request.message)
        if query_type == "identifier" and identifier:
            events = self.audit_manager.find_events(
                repo_path=request.repo_path,
                user_id=request.user_id,
                identifier=identifier,
            )
            empty_label = f"未找到 {identifier}"
        elif query_type == "verification_result":
            events = self.audit_manager.recent_events(
                repo_path=request.repo_path,
                user_id=request.user_id,
                event_type="verification_result",
            )
            empty_label = "当前 scope 没有 verification result"
        else:
            events = self.audit_manager.recent_events(
                repo_path=request.repo_path,
                user_id=request.user_id,
            )
            empty_label = "当前 scope 没有历史记录"
        status = "ok" if events else "empty"
        return AgentLoopResult(
            answer=format_recovery_answer(events, empty_label=empty_label),
            trace_events_internal=[
                TraceEvent(
                    event_type="audit_recovery",
                    status=status,
                    summary=f"query_type={query_type}; result_count={len(events)}",
                )
            ],
        )

    def _record_audit_and_return(
        self,
        request: AgentLoopRequest,
        result: AgentLoopResult,
    ) -> AgentLoopResult:
        if _skip_persistent_audit_for_result(result):
            return result
        events = [
            build_trace_event(
                status=_result_status(result),
                route=_route_from_trace(result.trace_events_internal),
                tool_count=len(result.tool_calls),
                trace_event_count=len(result.trace_events_internal),
            )
        ]
        for trace_event in result.trace_events_internal:
            event = build_event_from_trace(
                event_type=trace_event.event_type,
                status=trace_event.status,
                summary=trace_event.summary,
            )
            if event is not None:
                events.append(event)
        try:
            self.audit_manager.record_events(
                repo_path=request.repo_path,
                user_id=request.user_id,
                session_id=request.session_id,
                trace_id=request.trace_id,
                events=events,
            )
        except Exception:
            return AgentLoopResult(
                answer=result.answer,
                related_files=result.related_files,
                tool_calls=result.tool_calls,
                trace_events_internal=[
                    *result.trace_events_internal,
                    TraceEvent(
                        event_type="audit_persistence_failed",
                        status="error",
                        summary="persistent_audit=unavailable",
                    ),
                ],
            )
        return result


def _extract_search_keyword(message: str) -> str | None:
    tokens = TOKEN_PATTERN.findall(message)
    for token in tokens:
        if token.lower() in _ROUTING_STOPWORDS:
            continue
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
            "grounded answer",
            "model provider",
            "rerank",
            "context compression",
            "query rewrite",
            "patch",
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
            "support",
            "supports",
            "supported",
            "implemented",
            "available",
            "enabled",
            "current",
            "does",
            "do",
            "is",
            "are",
            "have",
            "has",
        )
    )


def _asks_about_unimplemented_v10_stack(message: str) -> bool:
    lower = message.lower()
    return any(
        term in lower
        for term in (
            "grounded answer",
            "model provider",
            "rerank",
            "context compression",
            "query rewrite",
        )
    )


def _capability_status_answer(message: str) -> str:
    lower = message.lower()
    asks_patch = "patch" in lower or "补丁" in message
    asks_memory = "memory" in lower or "记忆" in message
    asks_rewrite_or_rerank = any(term in lower for term in ("query rewrite", "rerank"))
    asks_vector_stack = any(
        term in lower
        for term in ("embedding", "milvus", "elasticsearch", "pgvector", "qdrant", "vector")
    )
    if asks_patch:
        return V16_CAPABILITY_STATUS_ANSWER
    if asks_memory and asks_vector_stack:
        return f"{VECTOR_CAPABILITY_STATUS_ANSWER}；{V13_CAPABILITY_STATUS_ANSWER}"
    if asks_memory and asks_rewrite_or_rerank:
        return f"{V12_CAPABILITY_STATUS_ANSWER}；{V13_CAPABILITY_STATUS_ANSWER}"
    if asks_memory:
        return V13_CAPABILITY_STATUS_ANSWER
    if asks_rewrite_or_rerank:
        return V12_CAPABILITY_STATUS_ANSWER
    if _asks_about_unimplemented_v10_stack(message):
        return V11_CAPABILITY_STATUS_ANSWER
    return VECTOR_CAPABILITY_STATUS_ANSWER


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
        if _is_absolute_path(file_path):
            continue
        citations.append(f"{file_path}:{start_line}-{end_line}")
    return ", ".join(citations)


def _format_audit_summary(audit_summary: dict[str, str | int | float]) -> str:
    return "; ".join(f"{key}={value}" for key, value in audit_summary.items())


def _channel_audit_summary(
    audit_summary: dict[str, str | int | float],
) -> dict[str, str | int | float]:
    hidden_prefixes = ("rewrite_", "rerank_")
    hidden_keys = {
        "evidence_items",
        "included_count",
        "omitted_count",
        "truncated_count",
        "budget_used_chars",
        "max_context_chars",
        "merged_results",
        "variant_count",
    }
    return {
        key: value
        for key, value in audit_summary.items()
        if key not in hidden_keys
        and not any(key.startswith(prefix) for prefix in hidden_prefixes)
    }


def _prefixed_audit_summary(
    audit_summary: dict[str, str | int | float],
    prefix: str,
) -> dict[str, str | int | float]:
    summary = {key: value for key, value in audit_summary.items() if key.startswith(prefix)}
    if prefix == "rewrite_" and "variant_count" in audit_summary:
        summary["variant_count"] = audit_summary["variant_count"]
    return summary


def _is_absolute_path(file_path: str) -> bool:
    return PureWindowsPath(file_path).is_absolute() or PurePosixPath(
        file_path
    ).is_absolute()


def _valid_repo_scope(repo_path: str) -> bool:
    try:
        return Path(repo_path).resolve(strict=True).is_dir()
    except (OSError, RuntimeError):
        return False


def _verification_answer_from_tool_result(tool_result) -> str:
    audit = tool_result.audit_summary
    status = str(audit.get("status", "failed"))
    exit_code_value = audit.get("exit_code")
    exit_code = None if exit_code_value == "" else int(exit_code_value)
    from app.verification.runner import VerificationRunResult

    result = VerificationRunResult(
        command_label=str(audit.get("command_label", "")),
        status=status,
        exit_code=exit_code,
        duration_ms=int(audit.get("duration_ms", 0)),
        stdout_excerpt=str(audit.get("stdout_excerpt", "")),
        stderr_excerpt=str(audit.get("stderr_excerpt", "")),
        timed_out=str(audit.get("timed_out", "false")) == "true",
        truncated=str(audit.get("truncated", "false")) == "true",
    )
    return format_verification_answer(result)


def _format_patch_verify_answer(
    apply_answer: str,
    verification_answer: str,
    verification_audit: dict[str, str | int | float],
) -> str:
    status = str(verification_audit.get("status", ""))
    suggestion = ""
    if status and status != "success":
        suggestion = " 下一步建议：请根据验证摘要生成新的 patch proposal 后再明确确认。"
    return f"{apply_answer} 验证结果：{verification_answer}{suggestion}"


def _verification_trace_summary(
    audit_summary: dict[str, str | int | float],
) -> str:
    public_keys = (
        "command_label",
        "status",
        "exit_code",
        "duration_ms",
        "timed_out",
        "truncated",
    )
    return _format_audit_summary(
        {key: audit_summary[key] for key in public_keys if key in audit_summary}
    )


def _is_real_provider(provider: ModelProvider) -> bool:
    return getattr(provider, "provider_name", "fake") != "fake"


def _result_status(result: AgentLoopResult) -> str:
    if any(event.status == "error" for event in result.trace_events_internal):
        return "error"
    if any(call.get("status") == "error" for call in result.tool_calls):
        return "error"
    return "ok"


def _route_from_trace(trace_events: list[TraceEvent]) -> str:
    for event in trace_events:
        if event.event_type == "audit_recovery":
            return "audit_recovery"
        if event.event_type == "memory_command":
            return "memory_command"
        if event.event_type == "long_task_command":
            return "long_task_command"
        if event.event_type == "assistant_control_surface":
            return "assistant_control_surface"
        if event.event_type in {
            "patch_command",
            "patch_verify_loop_started",
            "patch_proposal_summarized",
        }:
            return "patch"
        if event.event_type in {"verification_command", "verification_summarized"}:
            return "verification"
        if event.event_type == "request_routed":
            route = _summary_value(event.summary, "route")
            if route:
                return route
    return "unknown"


def _summary_value(summary: str, key: str) -> str:
    for part in summary.split(";"):
        if "=" not in part:
            continue
        current_key, value = part.split("=", 1)
        if current_key.strip() == key:
            return value.strip()
    return ""


def _skip_persistent_audit_for_result(result: AgentLoopResult) -> bool:
    return any(
        event.event_type == "audit_recovery" and event.status == "empty"
        for event in result.trace_events_internal
    )
