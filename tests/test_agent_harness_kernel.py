from pathlib import Path

from app.harness.kernel import (
    ApprovalGate,
    AgentLoop,
    AgentLoopRequest,
    PermissionDecision,
    PermissionPolicy,
    RequestRouter,
    RouteDecision,
    ToolSpec,
    ToolRegistry,
)
from app.rag.repo_rag import LexicalRepoRetriever
from app.tools.tool_executor import ToolExecutionResult


class FailingSearchExecutor:
    def search_code(self, repo_path: str, keyword: str) -> None:
        raise AssertionError("search_code must not be called when policy blocks")

    def search_repo_rag(self, repo_path: str, keyword: str, search_plan) -> None:
        raise AssertionError("search_repo_rag must not be called when policy blocks")


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


def test_default_tool_registry_marks_search_code_as_read_only_low_risk() -> None:
    registry = ToolRegistry.with_default_tools()

    assert registry.get("search_code") == ToolSpec(
        name="search_code",
        description="Search code in a repository using a read-only tool.",
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

    assert registry.get("search_code") is None
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
            name="search_code",
            description="Search code in a repository.",
            read_only=True,
            risk="low",
        )
    )

    assert decision == PermissionDecision(
        tool_name="search_code",
        status="allow",
        reason="allowed",
    )


def test_permission_policy_denies_non_read_only_or_high_risk_tools() -> None:
    policy = PermissionPolicy()

    assert policy.decide(None) == PermissionDecision(
        tool_name="search_code",
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
            name="search_code",
            description="Search code in a repository.",
            read_only=True,
            risk="high",
            requires_approval=True,
        )
    ) == PermissionDecision(
        tool_name="search_code",
        status="deny",
        reason="risk_not_allowed",
    )


def test_permission_policy_asks_for_approval_for_low_risk_approval_tool() -> None:
    decision = PermissionPolicy().decide(
        ToolSpec(
            name="search_code",
            description="Search code in a repository.",
            read_only=True,
            risk="low",
            requires_approval=True,
        )
    )

    assert decision == PermissionDecision(
        tool_name="search_code",
        status="ask",
        reason="approval_required",
    )
    assert ApprovalGate().evaluate(decision) is False


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
                    name="search_code",
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
                    name="search_code",
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
                    name="search_code",
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

    def search_repo_rag(
        self,
        repo_path: str,
        keyword: str,
        search_plan,
    ) -> ToolExecutionResult:
        self.called = True
        return ToolExecutionResult(
            tool_name="repo_rag",
            parameters={
                "keyword": keyword,
                "question_type": search_plan.question_type,
                "retrieval_mode": search_plan.retrieval_mode,
            },
            results=[],
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
        "tool_call",
        "tool_result",
        "retrieval_channels_summarized",
    ]


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


def test_agent_loop_uses_tool_executor_for_v8_repo_rag(tmp_path: Path) -> None:
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
            trace_id="trace_v8_rag",
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
    write_text(tmp_path / "README.md", "RepoPilot V8 uses lexical repo RAG.\n")
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
    assert "已实现 embedding" not in result.answer
    assert "已实现 Milvus" not in result.answer
    assert "已实现 ES" not in result.answer
    assert "已实现 memory" not in result.answer


def test_agent_loop_answers_lowercase_vector_status_questions(
    tmp_path: Path,
) -> None:
    write_text(tmp_path / "README.md", "RepoPilot V8 uses lexical repo RAG.\n")
    loop = AgentLoop()

    result = loop.run(
        AgentLoopRequest(
            message="embedding 和 memory 实现了吗?",
            repo_path=str(tmp_path),
            trace_id="trace_lower_vector_question",
        )
    )

    assert "未默认接入" in result.answer
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


def test_agent_loop_tool_call_records_v8_search_plan_metadata(
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
        and "fused_results=" in event.summary
        and "min_fused_score=0.5" in event.summary
        for event in result.trace_events_internal
    )
