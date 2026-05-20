# 交接给下一轮 Chat

## 分支状态

```text
当前工作分支：main
当前基线分支：main
当前活跃 OpenSpec change：无
```

## 当前项目状态

RepoPilot 当前定位为面向代码仓库分析任务的可控 Code Agent Harness，不是替代通用 AI IDE 的编程助手。V1-V8 已完成并进入长期规格/归档历史；当前暂无活跃 OpenSpec change。

当前主链路：

```text
API -> ChatService(trace_id) -> CodeAgent -> AgentLoop
  -> QueryUnderstanding/SearchPlan
  -> ToolRegistry -> PermissionPolicy -> ApprovalGate
  -> ToolExecutor(repo_rag) -> LexicalRepoRetriever -> file_tools
```

`/chat` 顶层响应仍保持现有 contract：`trace_id`、`answer`、`related_files`、`tool_calls`。V7 的权限和审批审计、V8 的 query understanding/retrieval 摘要只保留在内部 `trace_events_internal`，不作为 `/chat` 顶层字段暴露。

## 本轮完成

- 创建并实现 V7：`v7-permission-approval-gate`。
- 提交 V7：`7f1fc86 Add V7 permission approval gate`。
- 合并到 `main`：`Merge V7 permission approval gate`。
- 同步长期 spec：`openspec/specs/agent-loop-tool-execution/spec.md`。
- 归档 OpenSpec change：`openspec/changes/archive/2026-05-19-v7-permission-approval-gate/`。
- 恢复无活跃阶段 harness：
  - `.harness/allowed_files.md`
  - `.harness/review_checklist.md`

## 当前 V8 工作

- 创建并实现 V8：`v8-query-understanding-repo-rag`。
- 已同步 V8 阶段 harness：
  - `.harness/allowed_files.md`
  - `.harness/review_checklist.md`
- 已新增 deterministic `QueryUnderstanding/SearchPlan`。
- 已新增 lexical repo RAG：repo chunk、lexical scoring、dedup 和 citation。
- 已将 `/chat` repo_search 分支从简单 `search_code` 搜索升级为 `ToolExecutor(repo_rag) -> LexicalRepoRetriever`。
- V8 仍不实现 embedding、Milvus、Elasticsearch、PgVector、Qdrant、LLM rewrite、rerank、memory、SandboxRunner、skill execution 或多 agent orchestration。

## V7 边界

已实现：

- `ToolSpec.requires_approval`
- `PermissionDecision`
- `PermissionPolicy`
- 最小 `ApprovalGate`
- 权限优先级：未注册、非只读或非 `low` 风险 -> `deny`；否则 `requires_approval=True` -> `ask`；否则 -> `allow`。
- `ToolRegistry` 只登记和读取 `ToolSpec`，不保留独立 allow/deny gate。
- `AgentLoop` 负责记录 `permission_checked`、`tool_rejected` 和 `approval_required` trace event。
- `related_files` 只返回相对仓库路径，不返回本机绝对路径。

V7 不做：

- 不实现真实审批 UI。
- 不持久化审批记录。
- 不新增写文件、删文件或 shell 工具。
- 不实现 SandboxRunner。
- 不接真实 LLM。
- 不执行 skill。
- V7 本身不做 RAG、Memory、Reflection、eval、复杂多 Agent 或长任务 Agent；V8 已在后续阶段补上非向量化 lexical repo RAG。
- 不新增 `/chat` 顶层响应字段。

## 本轮验证

- `openspec validate v7-permission-approval-gate`：通过。
- `pytest tests/test_agent_harness_kernel.py`：16 passed。
- `pytest tests/test_chat_api.py`：6 passed。
- `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`：通过。
  - `pytest`：46 passed, 1 skipped。
  - `ruff check .`：All checks passed。
- `git diff --check`：通过，仅有 CRLF 换行提示。
- `openspec validate --all`：通过。

## 下一轮建议

1. 下一阶段可规划 V9：Embedding Retrieval + Hybrid Search。
2. 新阶段开始前同步 `.harness/allowed_files.md` 和 `.harness/review_checklist.md`。
3. 继续避免把真实审批流程、SandboxRunner、embedding/vector RAG、Memory、skill execution 或复杂多 Agent 提前塞进非对应阶段。

## V8 Handoff Update

当前工作分支：`main`（V8 已由 `codex/v8-query-understanding-repo-rag` 合并进入）

当前活跃 OpenSpec change：无；V8 已归档到 `openspec/changes/archive/2026-05-20-v8-query-understanding-repo-rag/`

V8 已实现 deterministic Query Understanding + 非向量化 Lexical Repo RAG：

- `app/rag/query_understanding.py`：生成 `SearchPlan`，包含问题类型、关键词、符号、路径提示和 `retrieval_mode=lexical`。
- `app/rag/repo_rag.py`：生成 repo chunk，执行 lexical scoring，返回 citation。
- `app/harness/kernel.py`：在 V7 权限/审批边界通过后通过 `ToolExecutor(repo_rag)` 执行 repo-local lexical RAG；`/chat` 顶层 contract 不变。

V8 不实现 embedding、Milvus、Elasticsearch、PgVector、Qdrant、LLM rewrite、rerank、memory、SandboxRunner、skill execution 或多 agent orchestration。

后续路线建议：V9 做 Embedding Retrieval + Hybrid Search，先做 provider/interface 和轻量本地实现，再决定是否引入 Milvus/ES；V10 做 Query Rewrite / Rerank / Grounded Answer / Context Budget；V11 做 Memory。
