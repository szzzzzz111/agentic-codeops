## Why

当前 RepoPilot 的 `/chat` 主链路已经具备 `AgentLoop -> ToolRegistry -> PermissionPolicy -> ApprovalGate -> ToolExecutor -> search_code` 的只读工具边界，但检索前仍然只是从用户消息里抽取一个可搜索 token。这样会跳过问题意图分析，也无法把证据组织成可引用的 repo-local RAG 上下文。

V8 将旧路线里的“大 Repo RAG Engineering”收窄为“Query Understanding + Lexical Repo RAG”。本阶段先建立非向量化的 repo-local RAG 骨架：理解问题、生成搜索计划、按代码文本 chunk 检索、返回 citation，并保持现有 `/chat` 顶层 contract 不变。

## What Changes

- 新增 deterministic `QueryUnderstanding` / `SearchPlan`，识别代码定位、实现解释、调用关系、测试/验证、文件摘要和未知泛问等问题类型。
- 从用户消息中提取文件名、路径片段、函数/类名、错误词、命令词和普通关键词，不接 LLM rewrite。
- 新增轻量 repo chunk 和 lexical retriever。chunk 包含 `chunk_id`、`file_path`、`start_line`、`end_line`、`text`。
- lexical scorer 使用 keyword、symbol、path、filename 和 exact token bonus，返回去重后的 citation。
- `AgentLoop` 在权限/审批边界通过后执行 repo-local lexical RAG，并把 citation 文件映射到现有 `related_files`。
- `/chat` 顶层字段保持 `trace_id`、`answer`、`related_files`、`tool_calls`，不新增必需字段。
- 内部 trace 可记录 query understanding 和 retrieval 摘要，但不暴露为新的 `/chat` 顶层字段。

## Roadmap Rebaseline

- V8: Query Understanding + Lexical Repo RAG
- V9: Embedding Retrieval + Hybrid Search
- V10: Query Rewrite / Rerank / Grounded Answer / Context Budget
- V11: Memory
- V12: Long Task / ReAct / Subagents
- V13: Personal Assistant Gateway

## Out of Scope

- 不实现 embedding、Milvus、Elasticsearch、PgVector 或任何向量库。
- 不实现 LLM query rewrite、LLM intent classification、rerank、memory、context compression。
- 不新增真实 LLM、shell、写文件工具、SandboxRunner、skill execution 或多 agent orchestration。
- 不把外部参考项目写成 RepoPilot runtime dependency 或当前能力。

## Capabilities

### New Capabilities

- `repo-query-understanding-rag`: repo-local query understanding、lexical chunk retrieval 和 citation contract。

### Modified Capabilities

- `agent-loop-tool-execution`: 工具执行通过现有权限/审批边界后，从单 keyword `search_code` 升级为 repo-local lexical RAG。

## Impact

- Code: `app/harness/kernel.py`, `app/rag/*`
- Tests: `tests/test_query_understanding.py`, `tests/test_repo_rag.py`, `tests/test_agent_harness_kernel.py`, `tests/test_chat_api.py`
- Docs: `README.md`, `docs/ARCHITECTURE.md`, `docs/PROGRESS.md`, `docs/FEATURE_LIST.json`, `HANDOFF_TO_NEXT_CHAT.md`
- Harness: `.harness/allowed_files.md`, `.harness/review_checklist.md`
