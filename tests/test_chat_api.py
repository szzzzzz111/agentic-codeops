from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def valid_payload(
    repo_path: Path,
    message: str = "帮我分析 UNIQUE_BUG_TOKEN",
) -> dict[str, str]:
    return {
        "user_id": "u001",
        "session_id": "s001",
        "message": message,
        "repo_path": str(repo_path),
    }


def test_chat_endpoint_returns_tool_results_for_unique_keyword(
    tmp_path: Path,
) -> None:
    write_text(tmp_path / "app" / "service.py", "UNIQUE_BUG_TOKEN = True\n")

    response = client.post("/chat", json=valid_payload(tmp_path))

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"trace_id", "answer", "related_files", "tool_calls"}
    assert body["trace_id"].startswith("trace_")
    assert "基于仓库证据" in body["answer"]
    assert "app/service.py:1-1" in body["answer"]
    assert body["related_files"] == ["app/service.py"]
    assert body["tool_calls"] == [
        {
            "tool_name": "repo_rag",
            "keyword": "UNIQUE_BUG_TOKEN",
            "question_type": "implementation_explanation",
            "retrieval_mode": "hybrid",
            "status": "success",
            "result_count": "1",
        }
    ]


def test_chat_endpoint_returns_empty_related_files_when_keyword_is_missing(
    tmp_path: Path,
) -> None:
    write_text(tmp_path / "app.py", "print('ok')\n")

    response = client.post("/chat", json=valid_payload(tmp_path))

    assert response.status_code == 200
    body = response.json()
    assert body["related_files"] == []
    assert body["tool_calls"] == [
        {
            "tool_name": "repo_rag",
            "keyword": "UNIQUE_BUG_TOKEN",
            "question_type": "implementation_explanation",
            "retrieval_mode": "hybrid",
            "status": "success",
            "result_count": "0",
        }
    ]


def test_chat_endpoint_does_not_return_sensitive_file_content(
    tmp_path: Path,
) -> None:
    write_text(tmp_path / "app.py", "UNIQUE_BUG_TOKEN = 'placeholder'\n")
    write_text(tmp_path / ".env", "UNIQUE_BUG_TOKEN=real-secret\n")

    response = client.post("/chat", json=valid_payload(tmp_path))

    assert response.status_code == 200
    body_text = response.text
    assert "real-secret" not in body_text
    body = response.json()
    assert ".env" not in body_text
    assert body["related_files"] == ["app.py"]
    assert body["tool_calls"] == [
        {
            "tool_name": "repo_rag",
            "keyword": "UNIQUE_BUG_TOKEN",
            "question_type": "implementation_explanation",
            "retrieval_mode": "hybrid",
            "status": "success",
            "result_count": "1",
        }
    ]


def test_chat_endpoint_sanitizes_tool_errors(tmp_path: Path) -> None:
    missing_repo = tmp_path / "missing"

    response = client.post("/chat", json=valid_payload(missing_repo))

    assert response.status_code == 200
    body_text = response.text
    assert str(missing_repo) not in body_text
    assert response.json()["tool_calls"] == [
        {
            "tool_name": "repo_rag",
            "keyword": "UNIQUE_BUG_TOKEN",
            "question_type": "implementation_explanation",
            "retrieval_mode": "hybrid",
            "status": "error",
            "result_count": "0",
            "error": "NotADirectoryError",
        }
    ]


def test_chat_endpoint_requires_repo_path_for_future_tool_compatibility() -> None:
    payload = {
        "user_id": "u001",
        "session_id": "s001",
        "message": "帮我分析 UNIQUE_BUG_TOKEN",
        "repo_path": "./mock_repo",
    }
    payload.pop("repo_path")

    response = client.post("/chat", json=payload)

    assert response.status_code == 422


def test_chat_endpoint_generates_unique_trace_ids(tmp_path: Path) -> None:
    first_response = client.post("/chat", json=valid_payload(tmp_path))
    second_response = client.post("/chat", json=valid_payload(tmp_path))

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert first_response.json()["trace_id"] != second_response.json()["trace_id"]


def test_chat_endpoint_keeps_contract_for_v8_repo_rag(tmp_path: Path) -> None:
    write_text(
        tmp_path / "app" / "harness" / "kernel.py",
        "class AgentLoop:\n"
        "    def run(self):\n"
        "        return search_code('UNIQUE_BUG_TOKEN')\n",
    )

    response = client.post(
        "/chat",
        json=valid_payload(
            tmp_path,
            "AgentLoop 在 app/harness/kernel.py 怎么调用 search_code?",
        ),
    )

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"trace_id", "answer", "related_files", "tool_calls"}
    assert "evidence_pack" not in body
    assert "provider_audit" not in body
    assert all("evidence_pack" not in tool_call for tool_call in body["tool_calls"])
    assert all("prompt" not in tool_call for tool_call in body["tool_calls"])
    assert all("provider" not in tool_call for tool_call in body["tool_calls"])
    assert body["related_files"] == ["app/harness/kernel.py"]
    assert "app/harness/kernel.py:1-" in body["answer"]


def test_chat_endpoint_memory_command_keeps_contract_and_redacts_paths(
    tmp_path: Path,
) -> None:
    response = client.post(
        "/chat",
        json=valid_payload(tmp_path, "记住：pref:language=中文"),
    )

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"trace_id", "answer", "related_files", "tool_calls"}
    assert body["answer"] == "已记住偏好：language。"
    assert body["related_files"] == []
    assert body["tool_calls"] == []
    assert str(tmp_path) not in response.text
    assert "memory.sqlite3" not in response.text


def test_chat_endpoint_long_task_create_keeps_contract_and_does_not_search(
    tmp_path: Path,
) -> None:
    write_text(tmp_path / "app.py", "task_abc = 'should not be searched'\n")

    response = client.post(
        "/chat",
        json=valid_payload(tmp_path, "创建长任务：查看 task_abc 的路由优先级"),
    )

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"trace_id", "answer", "related_files", "tool_calls"}
    assert "已创建长任务" in body["answer"]
    assert "task_id=task_" in body["answer"]
    assert body["related_files"] == []
    assert body["tool_calls"] == []
    assert str(tmp_path) not in response.text
    assert "tasks.sqlite3" not in response.text


def test_chat_endpoint_assistant_status_keeps_contract_and_does_not_create_state(
    tmp_path: Path,
) -> None:
    response = client.post(
        "/chat",
        json=valid_payload(tmp_path, "助手状态"),
    )

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"trace_id", "answer", "related_files", "tool_calls"}
    assert "当前能力" in body["answer"]
    assert "当前状态" in body["answer"]
    assert "下一步" in body["answer"]
    assert body["related_files"] == []
    assert body["tool_calls"] == []
    assert str(tmp_path) not in response.text
    assert "memory.sqlite3" not in response.text
    assert "tasks.sqlite3" not in response.text
    assert "evidence_pack" not in response.text
    assert "provider" not in response.text
    assert not (tmp_path / ".repopilot").exists()


def test_chat_endpoint_long_task_resume_returns_repo_rag_tool_call(
    tmp_path: Path,
) -> None:
    write_text(tmp_path / "app" / "harness" / "kernel.py", "class AgentLoop:\n    pass\n")
    create_response = client.post(
        "/chat",
        json=valid_payload(
            tmp_path,
            "创建长任务：分析 AgentLoop 在 app/harness/kernel.py 的实现",
        ),
    )
    task_id = create_response.json()["answer"].split("task_id=")[1].split("，")[0]

    response = client.post(
        "/chat",
        json=valid_payload(tmp_path, f"恢复任务 {task_id}"),
    )

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"trace_id", "answer", "related_files", "tool_calls"}
    assert "已推进任务" in body["answer"]
    assert body["related_files"] == ["app/harness/kernel.py"]
    assert body["tool_calls"][0]["tool_name"] == "repo_rag"
    assert body["tool_calls"][0]["status"] == "success"
    assert "scratch" not in response.text
    assert "provider" not in response.text


def test_docs_keep_stage_route_map_consistent() -> None:
    docs = [
        Path("README.md"),
        Path("docs/PROGRESS.md"),
        Path("docs/ARCHITECTURE.md"),
        Path("HANDOFF_TO_NEXT_CHAT.md"),
    ]
    combined = "\n".join(path.read_text(encoding="utf-8") for path in docs)

    assert "V10：Evidence Pack + Context Budget" in combined
    assert "V11：Grounded Answer / Model Provider Boundary" in combined
    assert "V12：Query Rewrite + Rerank" in combined
    assert "已归档至 V14：Long Task / ReAct Skeleton" in combined
    assert "V15：Assistant Control Surface" in combined
    assert "Assistant Control Surface" in combined
    assert "V10：Query Rewrite / Rerank / Context Budget" not in combined
    assert "V10 = Query Rewrite / Rerank / Context Budget" not in combined
    assert "V12 不默认启用真实 LLM rewrite/rerank" in combined


def test_long_term_specs_allow_repo_local_hybrid_rag() -> None:
    agent_loop_spec = Path(
        "openspec/specs/agent-loop-tool-execution/spec.md"
    ).read_text(encoding="utf-8")
    feature_list = Path("docs/FEATURE_LIST.json").read_text(encoding="utf-8")

    assert "repo-local hybrid RAG" in agent_loop_spec
    assert "不引入 embedding/vector RAG" not in agent_loop_spec
    assert "使用 embedding/vector RAG" not in agent_loop_spec
    assert "当前默认检索模式已由 V9 升级为 hybrid" in feature_list
