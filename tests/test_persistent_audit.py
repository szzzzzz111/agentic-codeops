from pathlib import Path

from app.audit.manager import AuditManager, AuditRecordInput
from app.audit.store import DEFAULT_RECENT_LIMIT, SQLiteAuditStore
from app.harness.kernel import AgentLoop, AgentLoopRequest
from app.memory.store import compute_repo_key
from app.providers.model_provider import ModelProviderResponse, ProviderCallMetrics
from app.tools.tool_executor import ToolExecutionResult


class FailingRepoRagExecutor:
    def search_repo_rag(self, repo_path: str, keyword: str, search_plan) -> None:
        raise AssertionError("repo_rag must not be called for recovery queries")


class SuccessfulVerificationExecutor:
    def verification_run(self, repo_path: str, command_label: str) -> ToolExecutionResult:
        return ToolExecutionResult(
            tool_name="verification_run",
            parameters={
                "command_label": command_label,
                "exit_code": "0",
                "duration_ms": "7",
                "timed_out": "false",
                "truncated": "false",
            },
            audit_summary={
                "command_label": command_label,
                "status": "success",
                "exit_code": 0,
                "duration_ms": 7,
                "timed_out": "false",
                "truncated": "false",
                "stdout_excerpt": "<repo> ok",
                "stderr_excerpt": "",
            },
        )


class FailingAuditManager(AuditManager):
    def record_events(self, **kwargs) -> None:
        raise OSError("audit unavailable")


class MetricsModelProvider:
    def generate(self, request):
        evidence = request.evidence[0]
        citation = (
            f"{evidence['file_path']}:{evidence['start_line']}-{evidence['end_line']}"
        )
        return ModelProviderResponse(
            answer=f"证据位于 {citation}",
            audit_summary={
                "provider": "metrics",
                "model": "test",
                "status": "success",
            },
            metrics=ProviderCallMetrics(
                availability="available",
                latency_ms=9,
                requested_model="test",
                returned_model="test",
                system_fingerprint="SECRET_FINGERPRINT",
                finish_reason="stop",
                finish_reason_status="complete",
                prompt_tokens=11,
                completion_tokens=3,
                total_tokens=14,
            ),
        )


def test_audit_store_scopes_events_by_user_and_repo(tmp_path: Path) -> None:
    store, repo_key = SQLiteAuditStore.for_repo(tmp_path / "repo_a")
    other_store, other_repo_key = SQLiteAuditStore.for_repo(tmp_path / "repo_b")

    store.insert_event(
        event_type="trace",
        user_id="u001",
        repo_key=repo_key,
        status="ok",
        summary="route=chat_only",
        payload={"route": "chat_only"},
    )
    store.insert_event(
        event_type="trace",
        user_id="u002",
        repo_key=repo_key,
        status="ok",
        summary="route=other_user",
        payload={"route": "other_user"},
    )
    other_store.insert_event(
        event_type="trace",
        user_id="u001",
        repo_key=other_repo_key,
        status="ok",
        summary="route=other_repo",
        payload={"route": "other_repo"},
    )

    events = store.recent_events(user_id="u001", repo_key=repo_key)

    assert len(events) == 1
    assert events[0].summary == "route=chat_only"


def test_audit_missing_store_read_does_not_create_state(tmp_path: Path) -> None:
    manager = AuditManager()

    events = manager.recent_events(repo_path=str(tmp_path), user_id="u001")

    assert events == []
    assert not (tmp_path / ".repopilot").exists()


def test_audit_recent_events_default_limit_without_pruning(tmp_path: Path) -> None:
    store, repo_key = SQLiteAuditStore.for_repo(tmp_path)
    for index in range(DEFAULT_RECENT_LIMIT + 5):
        store.insert_event(
            event_type="trace",
            user_id="u001",
            repo_key=repo_key,
            status="ok",
            summary=f"route={index}",
            payload={"index": index},
        )

    events = store.recent_events(user_id="u001", repo_key=repo_key)
    all_events = store.recent_events(
        user_id="u001",
        repo_key=repo_key,
        limit=DEFAULT_RECENT_LIMIT + 5,
    )

    assert len(events) == DEFAULT_RECENT_LIMIT
    assert len(all_events) == DEFAULT_RECENT_LIMIT + 5


def test_audit_manager_redacts_and_drops_dangerous_payload(tmp_path: Path) -> None:
    manager = AuditManager()
    manager.record_events(
        repo_path=str(tmp_path),
        user_id="u001",
        session_id="s001",
        trace_id="trace_secret",
        events=[
            AuditRecordInput(
                event_type="patch_attempt",
                status="error",
                summary="patch_status=failed; path=C:/Users/me/project/.repopilot/audit.sqlite3; API_KEY=abc",
                payload={
                    "diff_text": "--- a/app.py\n+++ b/app.py\n-secret\n+new\n",
                    "stdout": "full stdout should not persist",
                    "stderr": "full stderr should not persist",
                    "provider_prompt": "prompt should not persist",
                    "safe": "C:/Users/me/project/.repopilot/audit.sqlite3 API_TOKEN=abc",
                },
            )
        ],
    )

    store, repo_key = SQLiteAuditStore.for_existing_repo(tmp_path)
    events = store.recent_events(user_id="u001", repo_key=repo_key)
    stored_text = f"{events[0].summary} {events[0].payload}"

    assert "--- a/app.py" not in stored_text
    assert "full stdout" not in stored_text
    assert "provider_prompt" not in stored_text
    assert "C:/Users/me" not in stored_text
    assert "audit.sqlite3" not in stored_text
    assert "API_KEY=abc" not in stored_text
    assert "API_TOKEN=abc" not in stored_text


def test_agent_loop_persists_trace_and_verification_events(tmp_path: Path) -> None:
    loop = AgentLoop(tool_executor=SuccessfulVerificationExecutor())

    result = loop.run(
        AgentLoopRequest(
            message="run verify",
            repo_path=str(tmp_path),
            trace_id="trace_verify",
            user_id="u001",
            session_id="s001",
        )
    )

    assert result.tool_calls[0]["tool_name"] == "verification_run"
    store, repo_key = SQLiteAuditStore.for_existing_repo(tmp_path)
    events = store.recent_events(user_id="u001", repo_key=repo_key, limit=10)
    event_types = [event.event_type for event in events]
    assert "trace" in event_types
    assert "verification_result" in event_types
    assert all(str(tmp_path) not in event.summary for event in events)


def test_provider_metrics_do_not_enter_persistent_audit(tmp_path: Path) -> None:
    (tmp_path / "app.py").write_text(
        "UNIQUE_METRICS_TOKEN = True\n",
        encoding="utf-8",
    )
    loop = AgentLoop(model_provider=MetricsModelProvider())

    loop.run(
        AgentLoopRequest(
            message="UNIQUE_METRICS_TOKEN 在哪里",
            repo_path=str(tmp_path),
            trace_id="trace_metrics",
            user_id="u001",
            session_id="s001",
        )
    )

    store, repo_key = SQLiteAuditStore.for_existing_repo(tmp_path)
    events = store.recent_events(user_id="u001", repo_key=repo_key, limit=20)
    stored_text = " ".join(f"{event.summary} {event.payload}" for event in events)
    assert "SECRET_FINGERPRINT" not in stored_text
    assert "prompt_tokens" not in stored_text
    assert "total_tokens" not in stored_text


def test_agent_loop_recovery_query_reads_without_repo_rag_or_new_schema(
    tmp_path: Path,
) -> None:
    manager = AuditManager()
    manager.record_events(
        repo_path=str(tmp_path),
        user_id="u001",
        session_id="s001",
        trace_id="trace_existing",
        events=[
            AuditRecordInput(
                event_type="verification_result",
                status="ok",
                summary="command_label=verify; status=success",
                payload={"command_label": "verify", "status": "success"},
            )
        ],
    )
    loop = AgentLoop(tool_executor=FailingRepoRagExecutor())

    result = loop.run(
        AgentLoopRequest(
            message="最近验证结果",
            repo_path=str(tmp_path),
            trace_id="trace_recovery",
            user_id="u001",
            session_id="s001",
        )
    )

    assert "最近持久审计记录" in result.answer
    assert result.related_files == []
    assert result.tool_calls == []
    assert result.to_agent_result() == {
        "answer": result.answer,
        "related_files": [],
        "tool_calls": [],
    }


def test_agent_loop_recovery_missing_store_does_not_create_db(tmp_path: Path) -> None:
    loop = AgentLoop(tool_executor=FailingRepoRagExecutor())

    result = loop.run(
        AgentLoopRequest(
            message="恢复状态",
            repo_path=str(tmp_path),
            trace_id="trace_no_audit",
            user_id="u001",
            session_id="s001",
        )
    )

    assert "暂无持久审计记录" in result.answer
    assert not (tmp_path / ".repopilot").exists()


def test_agent_loop_audit_write_failure_does_not_break_chat(tmp_path: Path) -> None:
    loop = AgentLoop(audit_manager=FailingAuditManager())

    result = loop.run(
        AgentLoopRequest(
            message="hello",
            repo_path=str(tmp_path),
            trace_id="trace_audit_failure",
            user_id="u001",
            session_id="s001",
        )
    )

    assert result.related_files == []
    assert result.tool_calls == []
    assert any(
        event.event_type == "audit_persistence_failed"
        for event in result.trace_events_internal
    )
    assert str(tmp_path) not in result.answer


def test_agent_loop_recovery_trace_lookup_is_scoped(tmp_path: Path) -> None:
    manager = AuditManager()
    manager.record_events(
        repo_path=str(tmp_path),
        user_id="u001",
        session_id="s001",
        trace_id="trace_scope",
        events=[
            AuditRecordInput(
                event_type="trace",
                status="ok",
                summary="route=verification",
                payload={"route": "verification"},
            )
        ],
    )
    manager.record_events(
        repo_path=str(tmp_path),
        user_id="u002",
        session_id="s001",
        trace_id="trace_scope",
        events=[
            AuditRecordInput(
                event_type="trace",
                status="ok",
                summary="route=other_user",
                payload={"route": "other_user"},
            )
        ],
    )
    loop = AgentLoop()

    result = loop.run(
        AgentLoopRequest(
            message="查看 trace trace_scope",
            repo_path=str(tmp_path),
            trace_id="trace_lookup",
            user_id="u001",
            session_id="s001",
        )
    )

    assert "route=verification" in result.answer
    assert "other_user" not in result.answer
    assert compute_repo_key(tmp_path) not in result.answer


def test_audit_builds_worktree_lifecycle_event_without_paths() -> None:
    from app.audit.manager import build_event_from_trace

    event = build_event_from_trace(
        event_type="worktree_create_summarized",
        status="ok",
        summary="worktree_id=wt_20260607_abcdef; status=ready",
    )

    assert event is not None
    assert event.event_type == "worktree_event"
    assert event.related_id == "wt_20260607_abcdef"
