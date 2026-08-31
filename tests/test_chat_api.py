import json
import re
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def install_fake_worktree_create(monkeypatch, tmp_path: Path) -> None:
    from app.tools.tool_executor import ToolExecutionResult, ToolExecutor
    from app.worktrees.manager import WorktreeCreateResult

    def fake_worktree_create(self, repo_path: str, user_id: str, patch_id: str):
        return ToolExecutionResult(
            tool_name="worktree_create",
            parameters={"worktree_id": "wt_20260607_abcdef"},
            audit_summary={"status": "ready"},
            worktree_create_result=WorktreeCreateResult(
                created=True,
                status="ready",
                worktree_id="wt_20260607_abcdef",
                execution_repo_path=str(
                    tmp_path / ".repopilot" / "worktrees" / "wt_20260607_abcdef"
                ),
                base_commit="8c2b0f6",
                public_summary="worktree_id=wt_20260607_abcdef; status=ready",
            ),
        )

    monkeypatch.setattr(ToolExecutor, "worktree_create", fake_worktree_create)


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


def test_chat_endpoint_worktree_inventory_keeps_top_level_contract_and_no_state(
    tmp_path: Path,
) -> None:
    response = client.post("/chat", json=valid_payload(tmp_path, "worktree list"))

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"trace_id", "answer", "related_files", "tool_calls"}
    assert "当前 scope worktrees: 0" in body["answer"]
    assert body["related_files"] == []
    assert body["tool_calls"] == []
    assert not (tmp_path / ".repopilot").exists()


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
    assert (tmp_path / ".repopilot" / "audit.sqlite3").exists()
    assert not (tmp_path / ".repopilot" / "memory.sqlite3").exists()
    assert not (tmp_path / ".repopilot" / "tasks.sqlite3").exists()


def test_chat_endpoint_patch_capability_status_reports_current_truth(
    tmp_path: Path,
) -> None:
    response = client.post(
        "/chat",
        json=valid_payload(tmp_path, "is patch supported?"),
    )

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"trace_id", "answer", "related_files", "tool_calls"}
    assert "V19 提供 Persistent Audit / Recovery" in body["answer"]
    assert "V20-V23 提供隔离 worktree 生命周期" in body["answer"]
    assert "Verified Patch Promotion" in body["answer"]
    assert "默认不生成真实 diff" in body["answer"]
    assert "当前未实现 Persistent Audit / Recovery" not in body["answer"]
    assert body["related_files"] == []
    assert body["tool_calls"] == []


def test_chat_endpoint_v11_v12_capability_status_reports_current_truth(
    tmp_path: Path,
) -> None:
    response = client.post(
        "/chat",
        json=valid_payload(
            tmp_path,
            "Does RepoPilot support grounded answer or model provider?",
        ),
    )

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"trace_id", "answer", "related_files", "tool_calls"}
    assert "V11 提供 Grounded Answer 和 Model Provider Boundary" in body["answer"]
    assert "V12 提供 deterministic query rewrite 和 rerank" in body["answer"]
    assert "V13 提供 SQLite-backed Memory（PREF/LTM 和进程内 STM）" in body["answer"]
    assert "当前未实现 query rewrite、rerank、memory" not in body["answer"]
    assert "真实 LLM rewrite/rerank" in body["answer"]
    assert "向量 memory" in body["answer"]
    assert "context compression" in body["answer"]
    assert body["related_files"] == []
    assert body["tool_calls"] == []


def test_chat_endpoint_patch_proposal_keeps_contract_and_does_not_write(
    tmp_path: Path,
) -> None:
    write_text(tmp_path / "app.py", "old\n")

    response = client.post(
        "/chat",
        json=valid_payload(tmp_path, "请生成 patch 修改 app.py"),
    )

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"trace_id", "answer", "related_files", "tool_calls"}
    assert "无法生成可应用 patch" in body["answer"]
    assert "--- a/app.py" not in response.text
    assert body["related_files"] == ["app.py"]
    assert body["tool_calls"][0]["tool_name"] == "repo_rag"
    assert (tmp_path / "app.py").read_text(encoding="utf-8") == "old\n"


def test_chat_endpoint_confirm_patch_applies_without_running_verification(
    tmp_path: Path,
    monkeypatch,
) -> None:
    from app.memory.store import compute_repo_key
    from app.patching.apply import PatchApplyResult
    from app.patching.store import SQLitePatchStore
    from app.tools.tool_executor import ToolExecutionResult, ToolExecutor

    write_text(tmp_path / "app.py", "old\n")
    patch = SQLitePatchStore.for_repo(tmp_path).create_pending_patch(
        user_id="u001",
        repo_key=compute_repo_key(tmp_path),
        target_files=["app.py"],
        diff_text="--- a/app.py\n+++ b/app.py\n@@ -1 +1 @@\n-old\n+new\n",
        summary="update app",
    )
    install_fake_worktree_create(monkeypatch, tmp_path)

    def fake_patch_apply(self, repo_path: str, diff_text: str):
        return ToolExecutionResult(
            tool_name="patch_apply",
            parameters={},
            results=[{"file_path": "app.py", "line_number": 0, "line_text": ""}],
            audit_summary={"changed_files": 1},
            patch_apply_result=PatchApplyResult(
                applied=True,
                changed_files=["app.py"],
            ),
        )

    monkeypatch.setattr(ToolExecutor, "patch_apply", fake_patch_apply)

    response = client.post(
        "/chat",
        json=valid_payload(tmp_path, f"确认 patch {patch.patch_id}"),
    )

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"trace_id", "answer", "related_files", "tool_calls"}
    assert "已应用 patch" in body["answer"]
    assert body["tool_calls"] == [
        {
            "tool_name": "worktree_create",
            "worktree_id": "wt_20260607_abcdef",
            "status": "success",
            "result_count": "0",
        },
        {
            "tool_name": "patch_apply",
            "status": "success",
            "result_count": "1",
        },
    ]
    assert (tmp_path / "app.py").read_text(encoding="utf-8") == "old\n"
    assert "pytest" not in response.text
    assert "commit" not in response.text
    assert str(tmp_path) not in response.text


def test_chat_endpoint_patch_verify_loop_keeps_contract(
    tmp_path: Path,
    monkeypatch,
) -> None:
    from app.memory.store import compute_repo_key
    from app.patching.apply import PatchApplyResult
    from app.patching.store import SQLitePatchStore
    from app.tools.tool_executor import ToolExecutionResult, ToolExecutor

    write_text(tmp_path / "app.py", "old\n")
    patch = SQLitePatchStore.for_repo(tmp_path).create_pending_patch(
        user_id="u001",
        repo_key=compute_repo_key(tmp_path),
        target_files=["app.py"],
        diff_text="--- a/app.py\n+++ b/app.py\n@@ -1 +1 @@\n-old\n+new\n",
        summary="update app",
    )
    install_fake_worktree_create(monkeypatch, tmp_path)

    def fake_patch_apply(self, repo_path: str, diff_text: str):
        return ToolExecutionResult(
            tool_name="patch_apply",
            parameters={},
            results=[{"file_path": "app.py", "line_number": 0, "line_text": ""}],
            audit_summary={"changed_files": 1},
            patch_apply_result=PatchApplyResult(
                applied=True,
                changed_files=["app.py"],
            ),
        )

    def fake_verification_run(self, repo_path: str, command_label: str):
        return ToolExecutionResult(
            tool_name="verification_run",
            parameters={
                "command_label": command_label,
                "exit_code": "0",
                "duration_ms": "9",
                "timed_out": "false",
                "truncated": "false",
            },
            audit_summary={
                "command_label": command_label,
                "status": "success",
                "exit_code": 0,
                "duration_ms": 9,
                "timed_out": "false",
                "truncated": "false",
                "stdout_excerpt": "<repo> ok",
                "stderr_excerpt": "",
            },
        )

    monkeypatch.setattr(ToolExecutor, "patch_apply", fake_patch_apply)
    monkeypatch.setattr(ToolExecutor, "verification_run", fake_verification_run)

    response = client.post(
        "/chat",
        json=valid_payload(tmp_path, f"确认 patch {patch.patch_id} 并运行验证"),
    )

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"trace_id", "answer", "related_files", "tool_calls"}
    assert "已应用 patch" in body["answer"]
    assert "验证完成" in body["answer"]
    assert body["related_files"] == []
    assert body["tool_calls"] == [
        {
            "tool_name": "worktree_create",
            "worktree_id": "wt_20260607_abcdef",
            "status": "success",
            "result_count": "0",
        },
        {
            "tool_name": "patch_apply",
            "status": "success",
            "result_count": "1",
        },
        {
            "tool_name": "verification_run",
            "command_label": "verify",
            "exit_code": "0",
            "duration_ms": "9",
            "timed_out": "false",
            "truncated": "false",
            "status": "success",
            "result_count": "0",
        },
    ]
    assert "--- a/app.py" not in response.text
    assert str(tmp_path) not in response.text


def test_chat_endpoint_patch_verify_rejects_invalid_label_without_tool_calls(
    tmp_path: Path,
) -> None:
    from app.memory.store import compute_repo_key
    from app.patching.store import SQLitePatchStore

    patch = SQLitePatchStore.for_repo(tmp_path).create_pending_patch(
        user_id="u001",
        repo_key=compute_repo_key(tmp_path),
        target_files=["app.py"],
        diff_text="--- a/app.py\n+++ b/app.py\n@@ -1 +1 @@\n-old\n+new\n",
        summary="update app",
    )

    response = client.post(
        "/chat",
        json=valid_payload(
            tmp_path,
            f"确认 patch {patch.patch_id} 并运行 ruff --fix",
        ),
    )

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"trace_id", "answer", "related_files", "tool_calls"}
    assert "只支持固定验证命令" in body["answer"]
    assert body["related_files"] == []
    assert body["tool_calls"] == []
    assert "patch_apply" not in response.text
    assert "verification_run" not in response.text


def test_chat_endpoint_verification_keeps_contract_and_redacts_output(
    tmp_path: Path,
    monkeypatch,
) -> None:
    from app.tools.tool_executor import ToolExecutionResult, ToolExecutor

    def fake_verification_run(self, repo_path: str, command_label: str):
        return ToolExecutionResult(
            tool_name="verification_run",
            parameters={
                "command_label": command_label,
                "exit_code": "1",
                "duration_ms": "9",
                "timed_out": "false",
                "truncated": "true",
            },
            audit_summary={
                "command_label": command_label,
                "status": "failed",
                "exit_code": 1,
                "duration_ms": 9,
                "timed_out": "false",
                "truncated": "true",
                "stdout_excerpt": "<repo> failed <redacted-secret>",
                "stderr_excerpt": ".repopilot/<redacted> error",
            },
        )

    monkeypatch.setattr(ToolExecutor, "verification_run", fake_verification_run)

    response = client.post(
        "/chat",
        json=valid_payload(tmp_path, "运行验证"),
    )

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"trace_id", "answer", "related_files", "tool_calls"}
    assert "验证失败" in body["answer"]
    assert "truncated=true" in body["answer"]
    assert str(tmp_path) not in response.text
    assert ".repopilot/tasks.sqlite3" not in response.text
    assert "API_KEY=" not in response.text
    assert body["related_files"] == []
    assert body["tool_calls"] == [
        {
            "tool_name": "verification_run",
            "command_label": "verify",
            "exit_code": "1",
            "duration_ms": "9",
            "timed_out": "false",
            "truncated": "true",
            "status": "success",
            "result_count": "0",
        }
    ]


def test_chat_endpoint_verification_rejects_arbitrary_shell_without_repo_rag(
    tmp_path: Path,
) -> None:
    response = client.post(
        "/chat",
        json=valid_payload(tmp_path, "run verify | more"),
    )

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"trace_id", "answer", "related_files", "tool_calls"}
    assert "只支持固定验证命令" in body["answer"]
    assert body["related_files"] == []
    assert body["tool_calls"] == []
    assert "repo_rag" not in response.text


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


def test_docs_keep_current_information_architecture_consistent() -> None:
    docs = [
        Path("README.md"),
        Path("docs/PROGRESS.md"),
        Path("docs/ARCHITECTURE.md"),
        Path("HANDOFF_TO_NEXT_CHAT.md"),
    ]
    readme = docs[0].read_text(encoding="utf-8")
    architecture = docs[2].read_text(encoding="utf-8")
    progress = docs[1].read_text(encoding="utf-8")
    handoff = docs[3].read_text(encoding="utf-8")

    assert "## 当前快照" in readme
    assert "## 文档职责" in readme
    assert "### Verification Runner" not in readme
    assert "### Persistent Audit / Recovery" not in readme
    assert "### V19：Persistent Audit / Recovery" not in readme
    assert "## 阶段历史" not in readme
    assert "## 路线图" not in readme
    assert "## 系统上下文" in architecture
    assert "## 当前请求路由" in architecture
    assert "## 模块与代码映射" in architecture
    assert "## 状态与信任边界" in architecture
    assert "## 历史与规格入口" in architecture
    assert "app/harness/kernel.py" in architecture
    assert "app/worktrees/manager.py" in architecture
    assert "ToolRegistry -> PermissionPolicy -> ApprovalGate -> ToolExecutor" in architecture
    assert not re.search(r"(?m)^## V\d+", architecture)
    assert "## 当前状态" in progress
    assert "## 剩余债务" in progress
    assert "## 候选顺序" in progress
    assert "## 阶段索引" in progress
    assert "git status --short --branch" in handoff
    assert "openspec list" in handoff
    assert "Active OpenSpec change" not in handoff
    assert "当前只剩" not in handoff
    assert "尚未完成" not in handoff


def test_long_term_specs_allow_repo_local_hybrid_rag() -> None:
    agent_loop_spec = Path(
        "openspec/specs/agent-loop-tool-execution/spec.md"
    ).read_text(encoding="utf-8")
    feature_list = json.loads(Path("docs/FEATURE_LIST.json").read_text(encoding="utf-8"))
    feature_by_id = {item["id"]: item for item in feature_list}

    assert "repo-local hybrid RAG" in agent_loop_spec
    assert "不引入 embedding/vector RAG" not in agent_loop_spec
    assert "使用 embedding/vector RAG" not in agent_loop_spec
    assert "hybrid" in feature_by_id["v9-embedding-hybrid-search"]["description"]
    assert feature_by_id["v19-persistent-audit-recovery"]["passes"] is True
