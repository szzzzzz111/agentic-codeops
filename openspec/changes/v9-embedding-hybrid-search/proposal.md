## Why

V8 已经建立 deterministic Query Understanding 和 repo-local lexical RAG，但当前检索只能依赖关键词、符号和路径信号。V9 需要在不引入重型外部基础设施的前提下，补上轻量 embedding retrieval 和 hybrid fusion，让 RepoPilot 的检索链路具备可演进的语义召回边界。

同时，V10 原路线包含 Query Rewrite、Rerank、Grounded Answer 和 Context Budget，范围明显过大。V9 需要顺手把后续路线拆小：先让检索层稳定，再由后续阶段处理证据包、上下文预算和回答生成。

## What Changes

- 新增 embedding provider 抽象和轻量默认实现，用于生成可测试、确定性的 embedding 向量。
- 新增 repo-local embedding retrieval 通道，复用 V8 的安全文件边界、chunk 和 citation 约束。
- 保留 V8 lexical retrieval 作为一等检索通道，不用 embedding 替换 lexical。
- 新增 hybrid fusion，将 lexical score 与 embedding score 合并为稳定排序。
- `/chat` 顶层 contract 保持不变：`trace_id`、`answer`、`related_files`、`tool_calls`。
- 内部 trace/tool summary 可记录 retrieval channels、retrieval mode 和 fusion summary。
- 明确 V9 不默认引入 Milvus、Elasticsearch、PgVector、Qdrant 或真实外部 embedding 服务。
- 路线重排：V10 收窄为 Evidence Pack + Context Budget；V11 再处理 Grounded Answer / Model Provider Boundary；V12 再处理 Query Rewrite + Rerank。

## Capabilities

### New Capabilities

无新的顶层 capability。V9 的 embedding provider boundary、embedding retrieval 和 hybrid fusion 作为 `repo-query-understanding-rag` 既有检索能力的新增子能力进入 spec delta。

### Modified Capabilities

- `repo-query-understanding-rag`: 从 V8 的 lexical-only repo RAG 扩展为轻量 embedding provider boundary、repo-local embedding retrieval 和 hybrid fusion，同时保留只读、安全、citation 和 `/chat` contract 边界。

## Impact

- Code: `app/rag/`, `app/tools/tool_executor.py`, `app/harness/kernel.py`
- Tests: `tests/test_query_understanding.py`, `tests/test_repo_rag.py`, `tests/test_agent_harness_kernel.py`, `tests/test_chat_api.py`
- Docs: `README.md`, `docs/ARCHITECTURE.md`, `docs/PROGRESS.md`, `docs/FEATURE_LIST.json`, `HANDOFF_TO_NEXT_CHAT.md`
- Harness: `.harness/allowed_files.md`, `.harness/review_checklist.md`
- Specs: `openspec/changes/v9-embedding-hybrid-search/`, `openspec/specs/repo-query-understanding-rag/spec.md`
