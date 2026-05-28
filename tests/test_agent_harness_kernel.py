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
from app.providers.model_provider import ModelProviderResponse
from app.rag.repo_rag import LexicalRepoRetriever
from app.tools.tool_executor import ToolExecutionResult


class FailingSearchExecutor:
    def search_code(self, repo_path: str, keyword: str) -> None:
        raise AssertionError("search_code must not be called when policy blocks")

    def search_repo_rag(self, repo_path: str, keyword: str, search_plan) -> None:
        raise AssertionError("search_repo_rag must not be called when policy blocks")


class FailingRepoRagExecutor:
    def search_repo_rag(self, repo_path: str, keyword: str, search_plan) -> None:
        raise AssertionError("repo_rag must not be called for memory commands")


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
        "request_routed",
        "memory_command",
    ]
    assert "kind=PREF" in result.trace_events_internal[-1].summary
    assert str(tmp_path) not in result.trace_events_internal[-1].summary


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
