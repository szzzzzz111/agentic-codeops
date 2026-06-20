from pathlib import Path

from app.harness.kernel import (
    ApprovalGate,
    AgentLoop,
    AgentLoopRequest,
    PermissionDecision,
    PermissionPolicy,
    RequestRouter,
    RouteDecision,
    ToolInvocationContext,
    ToolSpec,
    ToolRegistry,
)
from app.memory.store import compute_repo_key
from app.patching.apply import PatchApplyResult
from app.patching.provider import FakePatchAuthoringProvider
from app.patching.store import PATCH_STATUS_PENDING, SQLitePatchStore
from app.providers.model_provider import ModelProviderResponse
from app.rag.repo_rag import LexicalRepoRetriever
from app.tools.tool_executor import ToolExecutionResult
from app.worktrees.manager import WorktreeCreateResult


class FailingSearchExecutor:
    def search_code(self, repo_path: str, keyword: str) -> None:
        raise AssertionError("search_code must not be called when policy blocks")

    def search_repo_rag(self, repo_path: str, keyword: str, search_plan) -> None:
        raise AssertionError("search_repo_rag must not be called when policy blocks")


class FailingRepoRagExecutor:
    def search_repo_rag(self, repo_path: str, keyword: str, search_plan) -> None:
        raise AssertionError("repo_rag must not be called for memory commands")


class FailingLongTaskExecutor:
    def search_repo_rag(self, repo_path: str, keyword: str, search_plan) -> None:
        raise AssertionError("repo_rag must not be called for long task control commands")


class FailingAssistantStatusExecutor:
    def search_repo_rag(self, repo_path: str, keyword: str, search_plan) -> None:
        raise AssertionError("repo_rag must not be called for assistant status")


class FailingPatchExecutor:
    def search_repo_rag(self, repo_path: str, keyword: str, search_plan) -> None:
        raise AssertionError("repo_rag must not be called for patch confirm")

    def patch_apply(self, repo_path: str, diff_text: str) -> None:
        raise AssertionError("patch_apply must not be called without valid confirmation")


class FailingVerificationExecutor:
    def search_repo_rag(self, repo_path: str, keyword: str, search_plan) -> None:
        raise AssertionError("repo_rag must not be called for verification requests")

    def verification_run(self, repo_path: str, command_label: str) -> None:
        raise AssertionError("verification_run must not be called without approval")


class SuccessfulVerificationExecutor:
    def __init__(self) -> None:
        self.command_labels: list[str] = []
        self.repo_paths: list[str] = []

    def verification_run(self, repo_path: str, command_label: str) -> ToolExecutionResult:
        self.repo_paths.append(repo_path)
        self.command_labels.append(command_label)
        return ToolExecutionResult(
            tool_name="verification_run",
            parameters={
                "command_label": command_label,
                "exit_code": "0",
                "duration_ms": "12",
                "timed_out": "false",
                "truncated": "false",
            },
            audit_summary={
                "command_label": command_label,
                "status": "success",
                "exit_code": 0,
                "duration_ms": 12,
                "timed_out": "false",
                "truncated": "false",
            },
        )


class RecordingPatchVerifyExecutor:
    def __init__(
        self,
        *,
        patch_applied: bool = True,
        worktree_path: str = "",
    ) -> None:
        self.patch_applied = patch_applied
        self.worktree_path = worktree_path
        self.calls: list[str] = []
        self.command_labels: list[str] = []
        self.patch_repo_paths: list[str] = []
        self.verification_repo_paths: list[str] = []
        self.created_patch_ids: list[str] = []

    def worktree_create(
        self,
        repo_path: str,
        user_id: str,
        patch_id: str,
    ) -> ToolExecutionResult:
        self.calls.append("worktree_create")
        self.created_patch_ids.append(patch_id)
        return ToolExecutionResult(
            tool_name="worktree_create",
            parameters={"worktree_id": "wt_20260607_abcdef"},
            audit_summary={"status": "ready"},
            worktree_create_result=WorktreeCreateResult(
                created=True,
                status="ready",
                reason="",
                worktree_id="wt_20260607_abcdef",
                execution_repo_path=self.worktree_path,
                base_commit="8c2b0f6",
                public_summary="worktree_id=wt_20260607_abcdef; status=ready",
            ),
        )

    def patch_apply(self, repo_path: str, diff_text: str) -> ToolExecutionResult:
        self.calls.append("patch_apply")
        self.patch_repo_paths.append(repo_path)
        result = PatchApplyResult(
            applied=self.patch_applied,
            changed_files=["app.py"] if self.patch_applied else [],
            error=None if self.patch_applied else "context_mismatch",
        )
        return ToolExecutionResult(
            tool_name="patch_apply",
            parameters={},
            results=[
                {"file_path": "app.py", "line_number": 0, "line_text": ""}
            ]
            if self.patch_applied
            else [],
            error=None if self.patch_applied else "context_mismatch",
            audit_summary={"changed_files": 1 if self.patch_applied else 0},
            patch_apply_result=result,
        )

    def verification_run(self, repo_path: str, command_label: str) -> ToolExecutionResult:
        self.calls.append("verification_run")
        self.verification_repo_paths.append(repo_path)
        self.command_labels.append(command_label)
        return ToolExecutionResult(
            tool_name="verification_run",
            parameters={
                "command_label": command_label,
                "exit_code": "0",
                "duration_ms": "12",
                "timed_out": "false",
                "truncated": "false",
            },
            audit_summary={
                "command_label": command_label,
                "status": "success",
                "exit_code": 0,
                "duration_ms": 12,
                "timed_out": "false",
                "truncated": "false",
            },
        )


class FailingWorktreeCreateExecutor:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def worktree_create(
        self,
        repo_path: str,
        user_id: str,
        patch_id: str,
    ) -> ToolExecutionResult:
        self.calls.append("worktree_create")
        return ToolExecutionResult(
            tool_name="worktree_create",
            parameters={},
            error="workspace_not_clean",
            audit_summary={"status": "create_failed"},
            worktree_create_result=WorktreeCreateResult(
                created=False,
                status="create_failed",
                reason="workspace_not_clean",
                public_summary="worktree 创建失败：主工作区必须干净。",
            ),
        )

    def patch_apply(self, repo_path: str, diff_text: str) -> None:
        raise AssertionError("patch_apply must not run after worktree create failure")

    def verification_run(self, repo_path: str, command_label: str) -> None:
        raise AssertionError("verification_run must not run after worktree create failure")


class RecordingVerificationContextPolicy(PermissionPolicy):
    def __init__(self) -> None:
        self.verification_contexts: list[ToolInvocationContext | None] = []
        self.worktree_contexts: list[ToolInvocationContext | None] = []

    def decide(self, tool_spec, tool_name="repo_rag", context=None):
        if tool_name == "worktree_create":
            self.worktree_contexts.append(context)
        if tool_name == "verification_run":
            self.verification_contexts.append(context)
        return super().decide(tool_spec, tool_name=tool_name, context=context)


class SuccessfulLongTaskExecutor:
    def __init__(self) -> None:
        self.keywords: list[str] = []

    def search_repo_rag(self, repo_path: str, keyword: str, search_plan) -> ToolExecutionResult:
        self.keywords.append(keyword)
        return ToolExecutionResult(
            tool_name="repo_rag",
            parameters={
                "keyword": keyword,
                "question_type": search_plan.question_type,
                "retrieval_mode": search_plan.retrieval_mode,
            },
            results=[
                {
                    "file_path": "app/harness/kernel.py",
                    "line_number": 1,
                    "line_text": "class AgentLoop:",
                    "start_line": 1,
                    "end_line": 1,
                }
            ],
        )


class NoCitationProvider:
    def generate(self, request):
        return ModelProviderResponse(
            answer="这是一个没有 citation 的回答。",
            audit_summary={
                "provider": "no_citation",
                "model": "test",
                "status": "success",
            },
        )


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_request_router_routes_search_tokens_to_repo_search() -> None:
    route = RequestRouter().route("帮我分析 UNIQUE_BUG_TOKEN")

    assert route == RouteDecision(
        route="repo_search",
        keyword="UNIQUE_BUG_TOKEN",
        reason="searchable_token",
    )


def test_request_router_routes_plain_chat_without_tools() -> None:
    route = RequestRouter().route("你好，请介绍一下项目")

    assert route == RouteDecision(
        route="chat_only",
        keyword=None,
        reason="no_searchable_token",
    )


def test_default_tool_registry_marks_repo_rag_as_read_only_low_risk() -> None:
    registry = ToolRegistry.with_default_tools()

    assert registry.get("repo_rag") == ToolSpec(
        name="repo_rag",
        description="Search a repository using read-only repo-local RAG.",
        read_only=True,
        risk="low",
        requires_approval=False,
    )


def test_tool_registry_only_stores_metadata_and_does_not_decide_policy() -> None:
    registry = ToolRegistry(
        [
            ToolSpec(
                name="write_file",
                description="Write a file.",
                read_only=False,
                risk="high",
            )
        ]
    )

    assert registry.get("repo_rag") is None
    assert registry.get("write_file") == ToolSpec(
        name="write_file",
        description="Write a file.",
        read_only=False,
        risk="high",
    )
    assert not hasattr(registry, "dispatch")
    assert not hasattr(registry, "is_allowed")
    assert not hasattr(registry, "rejection_reason")


def test_permission_policy_allows_low_risk_read_only_tool() -> None:
    decision = PermissionPolicy().decide(
        ToolSpec(
            name="repo_rag",
            description="Search code in a repository.",
            read_only=True,
            risk="low",
        )
    )

    assert decision == PermissionDecision(
        tool_name="repo_rag",
        status="allow",
        reason="allowed",
    )


def test_permission_policy_denies_non_read_only_or_high_risk_tools() -> None:
    policy = PermissionPolicy()

    assert policy.decide(None) == PermissionDecision(
        tool_name="repo_rag",
        status="deny",
        reason="not_registered",
    )
    assert policy.decide(
        ToolSpec(
            name="write_file",
            description="Write a file.",
            read_only=False,
            risk="low",
        )
    ) == PermissionDecision(
        tool_name="write_file",
        status="deny",
        reason="not_read_only",
    )
    assert policy.decide(
        ToolSpec(
            name="repo_rag",
            description="Search code in a repository.",
            read_only=True,
            risk="high",
            requires_approval=True,
        )
    ) == PermissionDecision(
        tool_name="repo_rag",
        status="deny",
        reason="risk_not_allowed",
    )


def test_permission_policy_asks_for_approval_for_low_risk_approval_tool() -> None:
    decision = PermissionPolicy().decide(
        ToolSpec(
            name="repo_rag",
            description="Search code in a repository.",
            read_only=True,
            risk="low",
            requires_approval=True,
        )
    )

    assert decision == PermissionDecision(
        tool_name="repo_rag",
        status="ask",
        reason="approval_required",
    )
    assert ApprovalGate().evaluate(decision) is False


def test_permission_policy_allows_patch_apply_only_via_confirmation_context() -> None:
    policy = PermissionPolicy()
    gate = ApprovalGate()
    spec = ToolSpec(
        name="patch_apply",
        description="Apply a confirmed patch.",
        read_only=False,
        risk="write",
        requires_approval=True,
    )
    context = ToolInvocationContext(
        tool_name="patch_apply",
        user_id="u001",
        repo_key="repo_a",
        intent="patch_apply",
        patch_id="patch_20260531_abcdef",
        confirmed=True,
        patch_status="pending",
        diff_hash_match=True,
        expires_at_valid=True,
        scope_valid=True,
    )

    decision = policy.decide(spec, tool_name="patch_apply", context=context)

    assert decision == PermissionDecision(
        tool_name="patch_apply",
        status="ask",
        reason="approval_required",
    )
    assert gate.evaluate(decision, context=context) is True
    assert policy.decide(spec, tool_name="patch_apply").status == "deny"
    assert ApprovalGate().evaluate(
        PermissionDecision("repo_rag", "ask", "approval_required")
    ) is False


def test_permission_policy_allows_verification_run_only_via_context() -> None:
    policy = PermissionPolicy()
    gate = ApprovalGate()
    spec = ToolSpec(
        name="verification_run",
        description="Run a whitelisted verification command.",
        read_only=False,
        risk="write",
        requires_approval=True,
    )
    context = ToolInvocationContext(
        tool_name="verification_run",
        intent="verification_run",
        command_label="verify",
        confirmed=True,
        scope_valid=True,
    )

    decision = policy.decide(spec, tool_name="verification_run", context=context)

    assert decision == PermissionDecision(
        tool_name="verification_run",
        status="ask",
        reason="approval_required",
    )
    assert gate.evaluate(decision, context=context) is True
    assert policy.decide(spec, tool_name="verification_run").status == "deny"
    assert policy.decide(
        ToolSpec(
            name="write_file",
            description="Write a file.",
            read_only=False,
            risk="write",
            requires_approval=True,
        ),
        tool_name="write_file",
        context=context,
    ) == PermissionDecision(
        tool_name="write_file",
        status="deny",
        reason="not_read_only",
    )


def test_permission_policy_allows_worktree_create_only_via_context() -> None:
    policy = PermissionPolicy()
    gate = ApprovalGate()
    spec = ToolSpec(
        name="worktree_create",
        description="Create an isolated Git worktree for a confirmed patch.",
        read_only=False,
        risk="write",
        requires_approval=True,
    )
    context = ToolInvocationContext(
        tool_name="worktree_create",
        user_id="u001",
        repo_key="repo_a",
        intent="worktree_create",
        patch_id="patch_20260531_abcdef",
        confirmed=True,
        patch_status="pending",
        diff_hash_match=True,
        expires_at_valid=True,
        scope_valid=True,
    )

    decision = policy.decide(spec, tool_name="worktree_create", context=context)

    assert decision == PermissionDecision(
        tool_name="worktree_create",
        status="ask",
        reason="approval_required",
    )
    assert gate.evaluate(decision, context=context) is True
    assert policy.decide(spec, tool_name="worktree_create").status == "deny"


def test_agent_loop_rejects_search_when_tool_is_not_registered(tmp_path: Path) -> None:
    loop = AgentLoop(
        tool_registry=ToolRegistry(),
        tool_executor=FailingSearchExecutor(),
    )

    result = loop.run(
        AgentLoopRequest(
            message="帮我分析 UNIQUE_BUG_TOKEN",
            repo_path=str(tmp_path),
            trace_id="trace_missing_tool",
        )
    )

    assert result.related_files == []
    assert result.tool_calls == []
    assert [event.event_type for event in result.trace_events_internal] == [
        "request_routed",
        "permission_checked",
        "tool_rejected",
    ]
    assert result.trace_events_internal[-1].status == "error"
    assert "not_registered" in result.trace_events_internal[-1].summary
    assert result.answer == "仓库工具未通过权限策略校验，因此本次没有执行仓库工具。"


def test_agent_loop_rejects_search_when_tool_is_not_read_only(tmp_path: Path) -> None:
    loop = AgentLoop(
        tool_registry=ToolRegistry(
            [
                ToolSpec(
                    name="repo_rag",
                    description="Search code in a repository.",
                    read_only=False,
                    risk="low",
                )
            ]
        ),
        tool_executor=FailingSearchExecutor(),
    )

    result = loop.run(
        AgentLoopRequest(
            message="帮我分析 UNIQUE_BUG_TOKEN",
            repo_path=str(tmp_path),
            trace_id="trace_not_read_only",
        )
    )

    assert result.trace_events_internal[-1].summary.endswith("not_read_only")


def test_agent_loop_rejects_search_when_tool_risk_is_not_allowed(
    tmp_path: Path,
) -> None:
    loop = AgentLoop(
        tool_registry=ToolRegistry(
            [
                ToolSpec(
                    name="repo_rag",
                    description="Search code in a repository.",
                    read_only=True,
                    risk="high",
                )
            ]
        ),
        tool_executor=FailingSearchExecutor(),
    )

    result = loop.run(
        AgentLoopRequest(
            message="帮我分析 UNIQUE_BUG_TOKEN",
            repo_path=str(tmp_path),
            trace_id="trace_high_risk",
        )
    )

    assert result.trace_events_internal[-1].summary.endswith("risk_not_allowed")


def test_agent_loop_asks_for_approval_without_calling_tool(tmp_path: Path) -> None:
    loop = AgentLoop(
        tool_registry=ToolRegistry(
            [
                ToolSpec(
                    name="repo_rag",
                    description="Search code in a repository.",
                    read_only=True,
                    risk="low",
                    requires_approval=True,
                )
            ]
        ),
        tool_executor=FailingSearchExecutor(),
    )

    result = loop.run(
        AgentLoopRequest(
            message="帮我分析 UNIQUE_BUG_TOKEN",
            repo_path=str(tmp_path),
            trace_id="trace_approval_required",
        )
    )

    assert result.answer == "工具调用需要人工审批，因此本次没有执行仓库工具。"
    assert result.related_files == []
    assert result.tool_calls == []
    assert [event.event_type for event in result.trace_events_internal] == [
        "request_routed",
        "permission_checked",
        "approval_required",
    ]


class AbsolutePathSearchExecutor:
    def search_code(self, repo_path: str, keyword: str) -> ToolExecutionResult:
        return ToolExecutionResult(
            tool_name="search_code",
            parameters={"keyword": keyword},
            results=[
                {
                    "file_path": "C:/outside/project/app.py",
                    "line_number": 1,
                    "line_text": keyword,
                }
            ],
        )

    def search_repo_rag(
        self,
        repo_path: str,
        keyword: str,
        search_plan,
    ) -> ToolExecutionResult:
        return ToolExecutionResult(
            tool_name="repo_rag",
            parameters={
                "keyword": keyword,
                "question_type": search_plan.question_type,
                "retrieval_mode": search_plan.retrieval_mode,
            },
            results=[
                {
                    "file_path": "C:/outside/project/app.py",
                    "line_number": 1,
                    "line_text": keyword,
                    "start_line": 1,
                    "end_line": 1,
                }
            ],
        )


class RecordingRepoRagExecutor:
    def __init__(self) -> None:
        self.called = False
        self.search_plan = None

    def search_repo_rag(
        self,
        repo_path: str,
        keyword: str,
        search_plan,
    ) -> ToolExecutionResult:
        self.called = True
        self.search_plan = search_plan
        return ToolExecutionResult(
            tool_name="repo_rag",
            parameters={
                "keyword": keyword,
                "question_type": search_plan.question_type,
                "retrieval_mode": search_plan.retrieval_mode,
            },
            results=[],
        )


class MixedPathSearchExecutor:
    def search_code(self, repo_path: str, keyword: str) -> ToolExecutionResult:
        raise AssertionError("search_code should not be called")

    def search_repo_rag(
        self,
        repo_path: str,
        keyword: str,
        search_plan,
    ) -> ToolExecutionResult:
        return ToolExecutionResult(
            tool_name="repo_rag",
            parameters={
                "keyword": keyword,
                "question_type": search_plan.question_type,
                "retrieval_mode": search_plan.retrieval_mode,
            },
            results=[
                {
                    "file_path": "app/service.py",
                    "line_number": 1,
                    "line_text": keyword,
                    "start_line": 1,
                    "end_line": 1,
                },
                {
                    "file_path": "C:/outside/project/secret.py",
                    "line_number": 2,
                    "line_text": keyword,
                    "start_line": 2,
                    "end_line": 2,
                },
            ],
        )


def test_agent_loop_trace_summary_does_not_include_absolute_result_paths(
    tmp_path: Path,
) -> None:
    loop = AgentLoop(tool_executor=AbsolutePathSearchExecutor())

    result = loop.run(
        AgentLoopRequest(
            message="帮我分析 UNIQUE_BUG_TOKEN",
            repo_path=str(tmp_path),
            trace_id="trace_absolute_path",
        )
    )

    assert result.related_files == []
    assert all(
        "C:/outside/project/app.py" not in event.summary
        for event in result.trace_events_internal
    )


def test_agent_loop_runs_repo_search_with_trace_events(tmp_path: Path) -> None:
    write_text(tmp_path / "app" / "service.py", "UNIQUE_BUG_TOKEN = True\n")
    loop = AgentLoop()

    result = loop.run(
        AgentLoopRequest(
            message="帮我分析 UNIQUE_BUG_TOKEN",
            repo_path=str(tmp_path),
            trace_id="trace_kernel",
        )
    )

    assert "UNIQUE_BUG_TOKEN" in result.answer
    assert result.related_files == ["app/service.py"]
    assert result.tool_calls == [
        {
            "tool_name": "repo_rag",
            "keyword": "UNIQUE_BUG_TOKEN",
            "question_type": "implementation_explanation",
            "retrieval_mode": "hybrid",
            "status": "success",
            "result_count": "1",
        }
    ]
    assert [event.event_type for event in result.trace_events_internal] == [
        "request_routed",
        "permission_checked",
        "memory_summarized",
        "tool_call",
        "tool_result",
        "query_rewrite_summarized",
        "rerank_summarized",
        "retrieval_channels_summarized",
        "evidence_pack_summarized",
        "model_provider_summarized",
    ]


def test_agent_loop_memory_command_confirms_without_repo_rag(tmp_path: Path) -> None:
    loop = AgentLoop(tool_executor=FailingRepoRagExecutor())

    result = loop.run(
        AgentLoopRequest(
            message="记住：pref:language=中文",
            repo_path=str(tmp_path),
            trace_id="trace_memory_remember",
            user_id="u001",
            session_id="s001",
        )
    )

    assert result.answer == "已记住偏好：language。"
    assert result.related_files == []
    assert result.tool_calls == []
    assert [event.event_type for event in result.trace_events_internal] == [
        "memory_command",
    ]
    assert "kind=PREF" in result.trace_events_internal[-1].summary
    assert str(tmp_path) not in result.trace_events_internal[-1].summary


def test_agent_loop_answers_assistant_status_without_repo_rag(tmp_path: Path) -> None:
    loop = AgentLoop(tool_executor=FailingAssistantStatusExecutor())

    result = loop.run(
        AgentLoopRequest(
            message="助手状态",
            repo_path=str(tmp_path),
            trace_id="trace_assistant_status",
            user_id="u001",
            session_id="s001",
        )
    )

    assert "当前能力" in result.answer
    assert "当前状态" in result.answer
    assert "下一步" in result.answer
    assert result.related_files == []
    assert result.tool_calls == []
    assert [event.event_type for event in result.trace_events_internal] == [
        "assistant_control_surface",
    ]
    assert all(
        event.event_type != "permission_checked"
        for event in result.trace_events_internal
    )
    assert (tmp_path / ".repopilot" / "audit.sqlite3").exists()
    assert not (tmp_path / ".repopilot" / "memory.sqlite3").exists()
    assert not (tmp_path / ".repopilot" / "tasks.sqlite3").exists()


def test_agent_loop_handles_memory_command_before_router_and_long_task(
    tmp_path: Path,
) -> None:
    loop = AgentLoop(tool_executor=FailingRepoRagExecutor())

    result = loop.run(
        AgentLoopRequest(
            message="记住：pref:task_hint=创建长任务 task_xxx 时先确认目标",
            repo_path=str(tmp_path),
            trace_id="trace_memory_before_long_task",
            user_id="u001",
            session_id="s001",
        )
    )

    assert result.answer == "已记住偏好：task_hint。"
    assert result.related_files == []
    assert result.tool_calls == []
    assert [event.event_type for event in result.trace_events_internal] == [
        "memory_command",
    ]


def test_agent_loop_memory_command_still_precedes_assistant_status(
    tmp_path: Path,
) -> None:
    loop = AgentLoop(tool_executor=FailingRepoRagExecutor())

    result = loop.run(
        AgentLoopRequest(
            message="记住：pref:assistant_status=优先确认目标",
            repo_path=str(tmp_path),
            trace_id="trace_memory_before_assistant",
            user_id="u001",
            session_id="s001",
        )
    )

    assert result.answer == "已记住偏好：assistant_status。"
    assert [event.event_type for event in result.trace_events_internal] == [
        "memory_command",
    ]


def test_agent_loop_handles_long_task_command_before_router_keyword(
    tmp_path: Path,
) -> None:
    loop = AgentLoop(tool_executor=FailingLongTaskExecutor())

    result = loop.run(
        AgentLoopRequest(
            message="创建长任务：查看 task_abc 的路由优先级",
            repo_path=str(tmp_path),
            trace_id="trace_long_task_create",
            user_id="u001",
            session_id="s001",
        )
    )

    assert "已创建长任务" in result.answer
    assert "task_" in result.answer
    assert result.related_files == []
    assert result.tool_calls == []
    assert [event.event_type for event in result.trace_events_internal] == [
        "long_task_command",
    ]


def test_agent_loop_long_task_command_still_precedes_assistant_status(
    tmp_path: Path,
) -> None:
    loop = AgentLoop(tool_executor=FailingLongTaskExecutor())

    result = loop.run(
        AgentLoopRequest(
            message="创建长任务：查看助手状态",
            repo_path=str(tmp_path),
            trace_id="trace_long_task_before_assistant",
            user_id="u001",
            session_id="s001",
        )
    )

    assert "已创建长任务" in result.answer
    assert [event.event_type for event in result.trace_events_internal] == [
        "long_task_command",
    ]


def test_agent_loop_handles_patch_confirm_before_repo_search(tmp_path: Path) -> None:
    loop = AgentLoop(tool_executor=FailingPatchExecutor())

    result = loop.run(
        AgentLoopRequest(
            message="确认 patch patch_20260531_missing",
            repo_path=str(tmp_path),
            trace_id="trace_patch_confirm",
            user_id="u001",
            session_id="s001",
        )
    )

    assert "未找到可应用的 patch" in result.answer
    assert result.related_files == []
    assert result.tool_calls == []
    assert [event.event_type for event in result.trace_events_internal] == [
        "patch_command",
    ]


def test_agent_loop_runs_verification_after_patch_and_before_repo_search(
    tmp_path: Path,
) -> None:
    executor = SuccessfulVerificationExecutor()
    loop = AgentLoop(tool_executor=executor)

    result = loop.run(
        AgentLoopRequest(
            message="运行验证",
            repo_path=str(tmp_path),
            trace_id="trace_v17_verify",
            user_id="u001",
            session_id="s001",
        )
    )

    assert executor.command_labels == ["verify"]
    assert executor.repo_paths == [str(tmp_path)]
    assert "验证完成" in result.answer
    assert result.related_files == []
    assert result.tool_calls == [
        {
            "tool_name": "verification_run",
            "command_label": "verify",
            "exit_code": "0",
            "duration_ms": "12",
            "timed_out": "false",
            "truncated": "false",
            "status": "success",
            "result_count": "0",
        }
    ]
    assert [event.event_type for event in result.trace_events_internal] == [
        "verification_command",
        "permission_checked",
        "tool_result",
        "verification_summarized",
    ]


def test_agent_loop_rejects_unsafe_verification_syntax_before_repo_search(
    tmp_path: Path,
) -> None:
    loop = AgentLoop(tool_executor=FailingVerificationExecutor())

    result = loop.run(
        AgentLoopRequest(
            message="运行 pytest tests/test_chat_api.py",
            repo_path=str(tmp_path),
            trace_id="trace_v17_verify_reject",
            user_id="u001",
            session_id="s001",
        )
    )

    assert "只支持固定验证命令" in result.answer
    assert result.related_files == []
    assert result.tool_calls == []
    assert [event.event_type for event in result.trace_events_internal] == [
        "verification_command",
    ]


def test_agent_loop_patch_verify_combination_applies_then_runs_verification(
    tmp_path: Path,
) -> None:
    patch = SQLitePatchStore.for_repo(tmp_path).create_pending_patch(
        user_id="u001",
        repo_key=compute_repo_key(tmp_path),
        target_files=["app.py"],
        diff_text="--- a/app.py\n+++ b/app.py\n@@ -1 +1 @@\n-old\n+new\n",
        summary="update app",
    )
    worktree_path = str(tmp_path / ".repopilot" / "worktrees" / "wt_20260607_abcdef")
    executor = RecordingPatchVerifyExecutor(worktree_path=worktree_path)
    policy = RecordingVerificationContextPolicy()
    loop = AgentLoop(tool_executor=executor, permission_policy=policy)

    result = loop.run(
        AgentLoopRequest(
            message=f"确认 patch {patch.patch_id} 并运行验证",
            repo_path=str(tmp_path),
            trace_id="trace_v18_patch_verify",
            user_id="u001",
            session_id="s001",
        )
    )

    assert executor.calls == ["worktree_create", "patch_apply", "verification_run"]
    assert executor.patch_repo_paths == [worktree_path]
    assert executor.verification_repo_paths == [worktree_path]
    assert executor.command_labels == ["verify"]
    assert executor.created_patch_ids == [patch.patch_id]
    assert len(policy.worktree_contexts) == 1
    worktree_context = policy.worktree_contexts[0]
    assert worktree_context is not None
    assert worktree_context.tool_name == "worktree_create"
    assert worktree_context.intent == "worktree_create"
    assert worktree_context.patch_id == patch.patch_id
    assert len(policy.verification_contexts) == 1
    verification_context = policy.verification_contexts[0]
    assert verification_context is not None
    assert verification_context.tool_name == "verification_run"
    assert verification_context.intent == "verification_run"
    assert verification_context.command_label == "verify"
    assert verification_context.confirmed is True
    assert verification_context.scope_valid is True
    assert "已应用 patch" in result.answer
    assert "验证完成" in result.answer
    assert result.tool_calls[0]["tool_name"] == "worktree_create"
    assert result.tool_calls[1]["tool_name"] == "patch_apply"
    assert result.tool_calls[2]["tool_name"] == "verification_run"
    assert [event.event_type for event in result.trace_events_internal] == [
        "patch_verify_loop_started",
        "permission_checked",
        "worktree_create_summarized",
        "patch_command",
        "permission_checked",
        "tool_result",
        "patch_apply_summarized",
        "worktree_patch_summarized",
        "patch_verify_apply_summarized",
        "permission_checked",
        "tool_result",
        "patch_verify_verification_summarized",
        "worktree_verification_summarized",
    ]


def test_agent_loop_patch_verify_invalid_label_rejects_without_apply(
    tmp_path: Path,
) -> None:
    patch = SQLitePatchStore.for_repo(tmp_path).create_pending_patch(
        user_id="u001",
        repo_key=compute_repo_key(tmp_path),
        target_files=["app.py"],
        diff_text="--- a/app.py\n+++ b/app.py\n@@ -1 +1 @@\n-old\n+new\n",
        summary="update app",
    )
    executor = RecordingPatchVerifyExecutor()
    loop = AgentLoop(tool_executor=executor)

    result = loop.run(
        AgentLoopRequest(
            message=f"确认 patch {patch.patch_id} 并运行 pytest tests/test_chat_api.py",
            repo_path=str(tmp_path),
            trace_id="trace_v18_patch_verify_reject",
            user_id="u001",
            session_id="s001",
        )
    )

    assert "只支持固定验证命令" in result.answer
    assert executor.calls == []
    assert result.related_files == []
    assert result.tool_calls == []
    assert [event.event_type for event in result.trace_events_internal] == [
        "patch_verify_loop_started",
    ]


def test_agent_loop_patch_verify_does_not_run_verification_when_apply_fails(
    tmp_path: Path,
) -> None:
    patch = SQLitePatchStore.for_repo(tmp_path).create_pending_patch(
        user_id="u001",
        repo_key=compute_repo_key(tmp_path),
        target_files=["app.py"],
        diff_text="--- a/app.py\n+++ b/app.py\n@@ -1 +1 @@\n-old\n+new\n",
        summary="update app",
    )
    worktree_path = str(tmp_path / ".repopilot" / "worktrees" / "wt_20260607_abcdef")
    executor = RecordingPatchVerifyExecutor(
        patch_applied=False,
        worktree_path=worktree_path,
    )
    policy = RecordingVerificationContextPolicy()
    loop = AgentLoop(tool_executor=executor, permission_policy=policy)

    result = loop.run(
        AgentLoopRequest(
            message=f"确认 patch {patch.patch_id} 并运行验证",
            repo_path=str(tmp_path),
            trace_id="trace_v18_patch_verify_apply_failed",
            user_id="u001",
            session_id="s001",
        )
    )

    assert executor.calls == ["worktree_create", "patch_apply"]
    assert executor.patch_repo_paths == [worktree_path]
    assert policy.verification_contexts == []
    assert "应用失败" in result.answer
    assert "验证" not in result.answer
    assert result.tool_calls == [
        {
            "tool_name": "worktree_create",
            "worktree_id": "wt_20260607_abcdef",
            "status": "success",
            "result_count": "0",
        },
        {
            "tool_name": "patch_apply",
            "status": "error",
            "result_count": "0",
            "error": "context_mismatch",
        }
    ]


def test_agent_loop_patch_verify_stops_when_worktree_create_fails(
    tmp_path: Path,
) -> None:
    patch_store = SQLitePatchStore.for_repo(tmp_path)
    repo_key = compute_repo_key(tmp_path)
    patch = patch_store.create_pending_patch(
        user_id="u001",
        repo_key=repo_key,
        target_files=["app.py"],
        diff_text="--- a/app.py\n+++ b/app.py\n@@ -1 +1 @@\n-old\n+new\n",
        summary="update app",
    )
    executor = FailingWorktreeCreateExecutor()

    result = AgentLoop(tool_executor=executor).run(
        AgentLoopRequest(
            message=f"确认 patch {patch.patch_id} 并运行验证",
            repo_path=str(tmp_path),
            trace_id="trace_v20_worktree_create_failed",
            user_id="u001",
            session_id="s001",
        )
    )

    assert executor.calls == ["worktree_create"]
    assert "worktree 创建失败" in result.answer
    stored_patch = patch_store.get_patch(
        patch.patch_id,
        user_id="u001",
        repo_key=repo_key,
    )
    assert stored_patch is not None
    assert stored_patch.status == PATCH_STATUS_PENDING
    assert [call["tool_name"] for call in result.tool_calls] == ["worktree_create"]
    assert all(
        event.tool_name != "verification_run" for event in result.trace_events_internal
    )


def test_agent_loop_confirm_patch_runs_apply_inside_worktree(tmp_path: Path) -> None:
    patch = SQLitePatchStore.for_repo(tmp_path).create_pending_patch(
        user_id="u001",
        repo_key=compute_repo_key(tmp_path),
        target_files=["app.py"],
        diff_text="--- a/app.py\n+++ b/app.py\n@@ -1 +1 @@\n-old\n+new\n",
        summary="update app",
    )
    worktree_path = str(tmp_path / ".repopilot" / "worktrees" / "wt_20260607_abcdef")
    executor = RecordingPatchVerifyExecutor(worktree_path=worktree_path)
    policy = RecordingVerificationContextPolicy()
    loop = AgentLoop(tool_executor=executor, permission_policy=policy)

    result = loop.run(
        AgentLoopRequest(
            message=f"confirm patch {patch.patch_id}",
            repo_path=str(tmp_path),
            trace_id="trace_v20_patch_apply",
            user_id="u001",
            session_id="s001",
        )
    )

    assert executor.calls == ["worktree_create", "patch_apply"]
    assert executor.patch_repo_paths == [worktree_path]
    assert executor.verification_repo_paths == []
    assert len(policy.worktree_contexts) == 1
    assert policy.verification_contexts == []
    assert result.tool_calls[0]["tool_name"] == "worktree_create"
    assert result.tool_calls[1]["tool_name"] == "patch_apply"
    assert [event.event_type for event in result.trace_events_internal] == [
        "permission_checked",
        "worktree_create_summarized",
        "patch_command",
        "permission_checked",
        "tool_result",
        "patch_apply_summarized",
        "worktree_patch_summarized",
    ]


def test_agent_loop_worktree_status_query_uses_v21_safe_inspection(tmp_path: Path) -> None:
    from app.worktrees.store import SQLiteWorktreeStore

    store, repo_key = SQLiteWorktreeStore.for_repo(tmp_path)
    store.create_worktree(
        user_id="u001",
        repo_key=repo_key,
        worktree_id="wt_20260607_abcdef",
        patch_id="patch_20260607_abcdef",
        base_commit="8c2b0f6",
        status="patch_applied",
        changed_files=["app.py"],
    )

    result = AgentLoop().run(
        AgentLoopRequest(
            message="worktree status wt_20260607_abcdef",
            repo_path=str(tmp_path),
            trace_id="trace_v20_worktree_status",
            user_id="u001",
            session_id="s001",
        )
    )

    assert "worktree_id=wt_20260607_abcdef" in result.answer
    assert "status=patch_applied" in result.answer
    assert "changed_files=none" in result.answer
    assert "partial=true" in result.answer
    assert "app.py" not in result.answer
    assert str(tmp_path) not in result.answer
    assert result.tool_calls == []
    assert [event.event_type for event in result.trace_events_internal] == [
        "worktree_inspection"
    ]


def test_agent_loop_reports_current_patch_capability_without_repo_search(
    tmp_path: Path,
) -> None:
    loop = AgentLoop(
        tool_registry=ToolRegistry(),
        tool_executor=FailingSearchExecutor(),
    )

    result = loop.run(
        AgentLoopRequest(
            message="patch apply 实现了吗?",
            repo_path=str(tmp_path),
            trace_id="trace_v16_patch_status",
        )
    )

    assert "V16 提供 Safe Patch Authoring" in result.answer
    assert "V17 提供独立 Verification Runner" in result.answer
    assert "V18 提供明确组合确认下的 Patch + Verify Loop" in result.answer
    assert "V19 提供 Persistent Audit / Recovery" in result.answer
    assert "V20-V23 提供隔离 worktree 生命周期" in result.answer
    assert "Verified Patch Promotion" in result.answer
    assert "自动 commit/push" in result.answer
    assert "默认不生成真实 diff" in result.answer
    assert "当前未实现 Persistent Audit / Recovery" not in result.answer
    assert "Worktree Isolation 未实现" not in result.answer
    assert result.related_files == []
    assert result.tool_calls == []


def test_agent_loop_model_provider_env_does_not_enable_real_patch_authoring(
    monkeypatch,
) -> None:
    monkeypatch.setenv("REPOPILOT_MODEL_PROVIDER", "openai_compatible")
    monkeypatch.setenv("REPOPILOT_MODEL_BASE_URL", "https://model.example/v1")
    monkeypatch.setenv("REPOPILOT_MODEL_API_KEY", "test-key")
    monkeypatch.setenv("REPOPILOT_MODEL_NAME", "test-model")

    loop = AgentLoop()

    assert isinstance(loop.patch_manager.provider, FakePatchAuthoringProvider)


def test_agent_loop_resumes_one_long_task_step_through_repo_rag(
    tmp_path: Path,
) -> None:
    executor = SuccessfulLongTaskExecutor()
    loop = AgentLoop(tool_executor=executor)
    create_result = loop.run(
        AgentLoopRequest(
            message="创建长任务：分析 AgentLoop 在 app/harness/kernel.py 的实现",
            repo_path=str(tmp_path),
            trace_id="trace_long_task_seed",
            user_id="u001",
            session_id="s001",
        )
    )
    task_id = create_result.answer.split("task_id=")[1].split("，")[0]

    result = loop.run(
        AgentLoopRequest(
            message=f"恢复任务 {task_id}",
            repo_path=str(tmp_path),
            trace_id="trace_long_task_resume",
            user_id="u001",
            session_id="s002",
        )
    )

    assert "已推进任务" in result.answer
    assert result.related_files == ["app/harness/kernel.py"]
    assert result.tool_calls == [
        {
            "tool_name": "repo_rag",
            "keyword": executor.keywords[0],
            "question_type": "implementation_explanation",
            "retrieval_mode": "hybrid",
            "status": "success",
            "result_count": "1",
        }
    ]
    assert [event.event_type for event in result.trace_events_internal][:4] == [
        "long_task_command",
        "permission_checked",
        "tool_call",
        "tool_result",
    ]


def test_agent_loop_blocks_long_task_when_resume_has_no_results(
    tmp_path: Path,
) -> None:
    executor = RecordingRepoRagExecutor()
    loop = AgentLoop(tool_executor=executor)
    create_result = loop.run(
        AgentLoopRequest(
            message="创建长任务：定位 MissingSymbol",
            repo_path=str(tmp_path),
            trace_id="trace_long_task_empty_seed",
            user_id="u001",
            session_id="s001",
        )
    )
    task_id = create_result.answer.split("task_id=")[1].split("，")[0]

    result = loop.run(
        AgentLoopRequest(
            message=f"恢复任务 {task_id}",
            repo_path=str(tmp_path),
            trace_id="trace_long_task_empty_resume",
            user_id="u001",
            session_id="s001",
        )
    )

    assert "已阻塞任务" in result.answer
    assert result.related_files == []
    assert result.tool_calls == [
            {
                "tool_name": "repo_rag",
                "keyword": executor.search_plan.original_query,
                "question_type": "code_location",
                "retrieval_mode": "hybrid",
                "status": "success",
                "result_count": "0",
            }
    ]


def test_agent_loop_forget_command_returns_deleted_count(tmp_path: Path) -> None:
    loop = AgentLoop(tool_executor=FailingRepoRagExecutor())
    request_kwargs = {
        "repo_path": str(tmp_path),
        "user_id": "u001",
        "session_id": "s001",
    }
    loop.run(
        AgentLoopRequest(
            message="remember: pref:language=中文",
            trace_id="trace_memory_seed",
            **request_kwargs,
        )
    )

    result = loop.run(
        AgentLoopRequest(
            message="forget: language",
            trace_id="trace_memory_forget",
            **request_kwargs,
        )
    )

    assert result.answer == "已删除 1 条记忆。"
    assert result.related_files == []
    assert result.tool_calls == []
    assert "deleted_count=1" in result.trace_events_internal[-1].summary


def test_agent_loop_memory_command_fails_gracefully_for_missing_repo(
    tmp_path: Path,
) -> None:
    missing_repo = tmp_path / "missing"
    loop = AgentLoop(tool_executor=FailingRepoRagExecutor())

    result = loop.run(
        AgentLoopRequest(
            message="记住：project:stack=FastAPI",
            repo_path=str(missing_repo),
            trace_id="trace_memory_missing_repo",
            user_id="u001",
            session_id="s001",
        )
    )

    assert result.answer == "无法写入记忆：当前仓库记忆存储不可用。"
    assert result.related_files == []
    assert result.tool_calls == []
    assert str(missing_repo) not in result.trace_events_internal[-1].summary


def test_agent_loop_records_memory_read_summary_without_public_tool_leak(
    tmp_path: Path,
) -> None:
    write_text(tmp_path / "app" / "service.py", "UNIQUE_BUG_TOKEN = True\n")
    loop = AgentLoop()

    result = loop.run(
        AgentLoopRequest(
            message="帮我分析 UNIQUE_BUG_TOKEN",
            repo_path=str(tmp_path),
            trace_id="trace_memory_summary",
            user_id="u001",
            session_id="s001",
        )
    )

    assert any(
        event.event_type == "memory_summarized"
        and "memory_status=success" in event.summary
        and "repo_key_present=true" in event.summary
        for event in result.trace_events_internal
    )
    assert all("memory" not in tool_call for tool_call in result.tool_calls)


def test_agent_loop_allows_retrievers_without_channel_summary(
    tmp_path: Path,
) -> None:
    write_text(tmp_path / "app" / "service.py", "UNIQUE_BUG_TOKEN = True\n")
    loop = AgentLoop(repo_retriever=LexicalRepoRetriever())

    result = loop.run(
        AgentLoopRequest(
            message="帮我分析 UNIQUE_BUG_TOKEN",
            repo_path=str(tmp_path),
            trace_id="trace_lexical_fallback",
        )
    )

    assert result.related_files == ["app/service.py"]
    assert all(
        event.event_type != "retrieval_channels_summarized"
        for event in result.trace_events_internal
    )


def test_request_router_routes_plain_english_chat_without_tools() -> None:
    route = RequestRouter().route("Hello, can you explain this project?")

    assert route == RouteDecision(
        route="chat_only",
        keyword=None,
        reason="no_searchable_token",
    )


def test_request_router_routes_capability_status_separately() -> None:
    route = RequestRouter().route("Does RepoPilot support grounded answer?")

    assert route == RouteDecision(
        route="capability_status",
        keyword="capability_status",
        reason="capability_status_question",
    )


def test_agent_loop_uses_tool_executor_for_repo_rag(tmp_path: Path) -> None:
    executor = RecordingRepoRagExecutor()
    loop = AgentLoop(tool_executor=executor)

    loop.run(
        AgentLoopRequest(
            message="帮我分析 UNIQUE_BUG_TOKEN",
            repo_path=str(tmp_path),
            trace_id="trace_executor_boundary",
        )
    )

    assert executor.called is True
    assert executor.search_plan.original_query == "帮我分析 UNIQUE_BUG_TOKEN"


def test_agent_loop_chat_only_does_not_call_tools(tmp_path: Path) -> None:
    loop = AgentLoop()

    result = loop.run(
        AgentLoopRequest(
            message="你好，请介绍一下项目",
            repo_path=str(tmp_path),
            trace_id="trace_chat",
        )
    )

    assert result.related_files == []
    assert result.tool_calls == []
    assert "没有调用仓库工具" in result.answer
    assert [event.event_type for event in result.trace_events_internal] == [
        "request_routed",
    ]
    assert all(
        event.event_type != "permission_checked"
        for event in result.trace_events_internal
    )


def test_agent_loop_result_adapts_to_chat_contract(tmp_path: Path) -> None:
    write_text(tmp_path / "app" / "service.py", "UNIQUE_BUG_TOKEN = True\n")
    loop = AgentLoop()

    result = loop.run(
        AgentLoopRequest(
            message="帮我分析 UNIQUE_BUG_TOKEN",
            repo_path=str(tmp_path),
            trace_id="trace_contract",
        )
    )

    assert result.to_agent_result() == {
        "answer": result.answer,
        "related_files": result.related_files,
        "tool_calls": result.tool_calls,
    }


def test_v6_kernel_does_not_expose_future_runtime_components() -> None:
    loop = AgentLoop()

    assert not hasattr(loop, "provider")
    assert not hasattr(loop, "context_builder")
    assert not hasattr(loop, "skill_registry")
    assert not hasattr(loop, "session_store")


def test_agent_loop_records_query_understanding_before_repo_retrieval(
    tmp_path: Path,
) -> None:
    write_text(
        tmp_path / "app" / "harness" / "kernel.py",
        "class AgentLoop:\n"
        "    def run(self):\n"
        "        return search_code('UNIQUE_BUG_TOKEN')\n",
    )
    loop = AgentLoop()

    result = loop.run(
        AgentLoopRequest(
            message="AgentLoop 在 app/harness/kernel.py 怎么调用 search_code?",
            repo_path=str(tmp_path),
            trace_id="trace_repo_rag",
        )
    )

    assert result.related_files == ["app/harness/kernel.py"]
    assert any(
        event.event_type == "query_understood"
        and "implementation_explanation" in event.summary
        for event in result.trace_events_internal
    )
    assert "app/harness/kernel.py:1-" in result.answer


def test_agent_loop_does_not_claim_vector_infrastructure_is_implemented(
    tmp_path: Path,
) -> None:
    write_text(tmp_path / "README.md", "RepoPilot uses repo RAG.\n")
    loop = AgentLoop()

    result = loop.run(
        AgentLoopRequest(
            message="现在实现 embedding、Milvus、ES、memory 了吗?",
            repo_path=str(tmp_path),
            trace_id="trace_vector_question",
        )
    )

    assert "V9 提供轻量 embedding retrieval 和 hybrid search" in result.answer
    assert "规划提供" not in result.answer
    assert "未默认接入" in result.answer
    assert "V13 提供 SQLite-backed PREF/LTM 和进程内 STM" in result.answer
    assert "已实现 embedding" not in result.answer
    assert "已实现 Milvus" not in result.answer
    assert "已实现 ES" not in result.answer
    assert "已实现 memory" not in result.answer
    assert result.related_files == []
    assert result.tool_calls == []


def test_agent_loop_answers_lowercase_vector_status_questions(
    tmp_path: Path,
) -> None:
    write_text(tmp_path / "README.md", "RepoPilot uses repo RAG.\n")
    loop = AgentLoop()

    result = loop.run(
        AgentLoopRequest(
            message="embedding 和 memory 实现了吗?",
            repo_path=str(tmp_path),
            trace_id="trace_lower_vector_question",
        )
    )

    assert "未默认接入" in result.answer
    assert "V13 提供 SQLite-backed PREF/LTM 和进程内 STM" in result.answer
    assert result.related_files == []
    assert result.tool_calls == []


def test_agent_loop_reports_v13_memory_capability_status_without_repo_search(
    tmp_path: Path,
) -> None:
    loop = AgentLoop(
        tool_registry=ToolRegistry(),
        tool_executor=FailingSearchExecutor(),
    )

    result = loop.run(
        AgentLoopRequest(
            message="memory 实现了吗?",
            repo_path=str(tmp_path),
            trace_id="trace_v13_memory_status",
        )
    )

    assert "V13 提供 SQLite-backed PREF/LTM 和进程内 STM" in result.answer
    assert "明确 memory 指令" in result.answer
    assert "未实现向量记忆" in result.answer
    assert result.related_files == []
    assert result.tool_calls == []


def test_agent_loop_answers_english_capability_status_without_repo_search(
    tmp_path: Path,
) -> None:
    loop = AgentLoop(
        tool_registry=ToolRegistry(),
        tool_executor=FailingSearchExecutor(),
    )

    result = loop.run(
        AgentLoopRequest(
            message="Does RepoPilot support grounded answer or model provider?",
            repo_path=str(tmp_path),
            trace_id="trace_english_capability",
        )
    )

    assert "V11 提供 Grounded Answer 和 Model Provider Boundary" in result.answer
    assert "默认 fake provider" in result.answer
    assert result.related_files == []
    assert result.tool_calls == []
    assert [event.event_type for event in result.trace_events_internal] == [
        "request_routed",
    ]


def test_agent_loop_reports_v11_capability_status_without_repo_search(
    tmp_path: Path,
) -> None:
    write_text(tmp_path / "README.md", "RepoPilot V10 has evidence pack.\n")
    loop = AgentLoop()

    result = loop.run(
        AgentLoopRequest(
            message="grounded answer、model provider 实现了吗?",
            repo_path=str(tmp_path),
            trace_id="trace_v10_status",
        )
    )

    assert "V11 提供 Grounded Answer 和 Model Provider Boundary" in result.answer
    assert "未实现 grounded answer" not in result.answer
    assert result.related_files == []
    assert result.tool_calls == []


def test_agent_loop_reports_v12_capability_status_without_repo_search(
    tmp_path: Path,
) -> None:
    write_text(tmp_path / "README.md", "RepoPilot V12 has rewrite and rerank.\n")
    loop = AgentLoop()

    result = loop.run(
        AgentLoopRequest(
            message="query rewrite、rerank、真实 LLM rewrite、memory 实现了吗?",
            repo_path=str(tmp_path),
            trace_id="trace_v12_status",
        )
    )

    assert "V12 提供 deterministic query rewrite 和 rerank" in result.answer
    assert "真实 LLM rewrite/rerank" in result.answer
    assert "V13 提供 SQLite-backed PREF/LTM 和进程内 STM" in result.answer
    assert result.related_files == []
    assert result.tool_calls == []


def test_capability_status_question_does_not_require_search_tool_registration(
    tmp_path: Path,
) -> None:
    loop = AgentLoop(
        tool_registry=ToolRegistry(),
        tool_executor=FailingSearchExecutor(),
    )

    result = loop.run(
        AgentLoopRequest(
            message="embedding 和 Milvus 实现了吗?",
            repo_path=str(tmp_path),
            trace_id="trace_capability_without_tool",
        )
    )

    assert "未默认接入" in result.answer
    assert result.related_files == []
    assert result.tool_calls == []
    assert [event.event_type for event in result.trace_events_internal] == [
        "request_routed",
    ]


def test_agent_loop_searches_repo_for_memory_symbol_location(
    tmp_path: Path,
) -> None:
    write_text(tmp_path / "memory_store.py", "class MemoryStore:\n    pass\n")
    loop = AgentLoop()

    result = loop.run(
        AgentLoopRequest(
            message="MemoryStore 在哪里实现?",
            repo_path=str(tmp_path),
            trace_id="trace_memory_symbol",
        )
    )

    assert result.related_files == ["memory_store.py"]
    assert "未实现 embedding" not in result.answer


def test_agent_loop_tool_call_records_hybrid_search_plan_metadata(
    tmp_path: Path,
) -> None:
    write_text(
        tmp_path / "app" / "harness" / "kernel.py",
        "class AgentLoop:\n"
        "    def run(self):\n"
        "        return search_code('UNIQUE_BUG_TOKEN')\n",
    )
    loop = AgentLoop()

    result = loop.run(
        AgentLoopRequest(
            message="AgentLoop 在 app/harness/kernel.py 怎么调用 search_code?",
            repo_path=str(tmp_path),
            trace_id="trace_tool_call_metadata",
        )
    )

    assert result.tool_calls == [
        {
            "tool_name": "repo_rag",
            "keyword": "AgentLoop",
            "question_type": "implementation_explanation",
            "retrieval_mode": "hybrid",
            "status": "success",
            "result_count": "1",
        }
    ]


def test_agent_loop_answer_filters_absolute_paths_from_citations(
    tmp_path: Path,
) -> None:
    loop = AgentLoop(tool_executor=MixedPathSearchExecutor())

    result = loop.run(
        AgentLoopRequest(
            message="帮我分析 UNIQUE_BUG_TOKEN",
            repo_path=str(tmp_path),
            trace_id="trace_mixed_paths",
        )
    )

    assert result.related_files == ["app/service.py"]
    assert "app/service.py:1-1" in result.answer
    assert "C:/outside/project/secret.py" not in result.answer


def test_agent_loop_records_hybrid_channel_audit_summary(tmp_path: Path) -> None:
    write_text(
        tmp_path / "app" / "service.py",
        "class PaymentService:\n"
        "    def capture_invoice(self):\n"
        "        return 'invoice captured'\n",
    )
    loop = AgentLoop()

    result = loop.run(
        AgentLoopRequest(
            message="PaymentService 在 app/service.py 怎么 capture_invoice?",
            repo_path=str(tmp_path),
            trace_id="trace_hybrid_audit",
        )
    )

    assert any(
        event.event_type == "retrieval_channels_summarized"
        and event.tool_name == "repo_rag"
        and "mode=hybrid" in event.summary
        and "lexical_results=" in event.summary
        and "embedding_results=" in event.summary
        and "anchored_embedding_results=" in event.summary
        and "fused_results=" in event.summary
        and "min_fused_score=0.35" in event.summary
        for event in result.trace_events_internal
    )


def test_agent_loop_records_rewrite_and_rerank_audit_without_public_leak(
    tmp_path: Path,
) -> None:
    write_text(
        tmp_path / "app" / "providers" / "model_provider.py",
        "class ModelProvider:\n"
        "    pass\n"
        "def load_model_provider_from_env():\n"
        "    return ModelProvider()\n",
    )
    write_text(
        tmp_path / "tests" / "test_model_provider.py",
        "def test_model_provider_fallback():\n"
        "    assert True\n",
    )
    loop = AgentLoop()

    result = loop.run(
        AgentLoopRequest(
            message="ModelProvider 在 app/providers/model_provider.py 怎么接入?",
            repo_path=str(tmp_path),
            trace_id="trace_v12_audit",
        )
    )

    assert result.tool_calls == [
        {
            "tool_name": "repo_rag",
            "keyword": "ModelProvider",
            "question_type": "implementation_explanation",
            "retrieval_mode": "hybrid",
            "status": "success",
            "result_count": "2",
        }
    ]
    assert all("variant" not in tool_call for tool_call in result.tool_calls)
    assert any(
        event.event_type == "query_rewrite_summarized"
        and "rewrite_provider=deterministic" in event.summary
        and "variant_count=" in event.summary
        for event in result.trace_events_internal
    )
    assert any(
        event.event_type == "rerank_summarized"
        and "rerank_provider=deterministic" in event.summary
        and "rerank_output_count=" in event.summary
        for event in result.trace_events_internal
    )
    assert all("C:/" not in event.summary for event in result.trace_events_internal)


def test_agent_loop_records_evidence_pack_summary_without_public_tool_leak(
    tmp_path: Path,
) -> None:
    write_text(tmp_path / "app" / "service.py", "UNIQUE_BUG_TOKEN = True\n")
    loop = AgentLoop()

    result = loop.run(
        AgentLoopRequest(
            message="帮我分析 UNIQUE_BUG_TOKEN",
            repo_path=str(tmp_path),
            trace_id="trace_evidence_pack",
        )
    )

    assert result.tool_calls == [
        {
            "tool_name": "repo_rag",
            "keyword": "UNIQUE_BUG_TOKEN",
            "question_type": "implementation_explanation",
            "retrieval_mode": "hybrid",
            "status": "success",
            "result_count": "1",
        }
    ]
    assert any(
        event.event_type == "evidence_pack_summarized"
        and "evidence_items=1" in event.summary
        and "included_count=1" in event.summary
        and "omitted_count=0" in event.summary
        and "truncated_count=0" in event.summary
        and "budget_used_chars=" in event.summary
        and "max_context_chars=4000" in event.summary
        for event in result.trace_events_internal
    )


def test_agent_loop_generates_grounded_answer_from_evidence_pack(
    tmp_path: Path,
) -> None:
    write_text(tmp_path / "app" / "service.py", "UNIQUE_BUG_TOKEN = True\n")
    loop = AgentLoop()

    result = loop.run(
        AgentLoopRequest(
            message="帮我分析 UNIQUE_BUG_TOKEN",
            repo_path=str(tmp_path),
            trace_id="trace_grounded_answer",
        )
    )

    assert "基于仓库证据" in result.answer
    assert "app/service.py:1-1" in result.answer
    assert any(
        event.event_type == "model_provider_summarized"
        and "provider=fake" in event.summary
        and "status=success" in event.summary
        for event in result.trace_events_internal
    )
    assert all("provider" not in tool_call for tool_call in result.tool_calls)


def test_agent_loop_falls_back_when_provider_answer_has_no_valid_citation(
    tmp_path: Path,
) -> None:
    write_text(tmp_path / "app" / "service.py", "UNIQUE_BUG_TOKEN = True\n")
    loop = AgentLoop(model_provider=NoCitationProvider())

    result = loop.run(
        AgentLoopRequest(
            message="帮我分析 UNIQUE_BUG_TOKEN",
            repo_path=str(tmp_path),
            trace_id="trace_grounded_fallback",
        )
    )

    assert result.answer == "无法基于当前仓库证据生成可靠回答。"
    assert any(
        event.event_type == "model_provider_summarized"
        and "fallback_reason=missing_citation" in event.summary
        for event in result.trace_events_internal
    )


def test_agent_loop_does_not_create_evidence_pack_on_tool_error(
    tmp_path: Path,
) -> None:
    missing_repo = tmp_path / "missing"
    loop = AgentLoop()

    result = loop.run(
        AgentLoopRequest(
            message="帮我分析 UNIQUE_BUG_TOKEN",
            repo_path=str(missing_repo),
            trace_id="trace_evidence_error",
        )
    )

    assert all(
        event.event_type != "evidence_pack_summarized"
        for event in result.trace_events_internal
    )
