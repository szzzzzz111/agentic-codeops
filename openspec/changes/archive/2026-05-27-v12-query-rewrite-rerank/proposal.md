## Why

V11 已经在 Evidence Pack / Context Budget 之后建立 Grounded Answer / Model Provider Boundary，但检索链路仍只使用单个 deterministic `SearchPlan` 执行 hybrid retrieval。对于代码仓库问题，用户的一句话常常同时包含定义、调用、配置和测试等多个证据视角；仅靠单次检索容易漏掉关键证据。

V12 需要在保持 grep-first, RAG-assisted 立场的前提下，引入 bounded deterministic multi-query rewrite 和 before-Evidence rerank：默认不调用真实 LLM、网络或 API key，但先把可替换边界、审计和 fallback 规则建好，为后续 V12.1 显式真实 provider 留接口。

## What Changes

- 新增 Query Rewrite Provider 边界，默认 deterministic provider 生成 `original` variant 和最多 3 条 Code Evidence query variants。
- 默认 variant id 固定为 `original`、`definition`、`usage`、`configuration`、`tests`，按 `definition -> usage -> configuration -> tests` 顺序生成并截断。
- 每个 variant 可以是独立 query，不只是原问题补词；但 V12 不允许 rewrite 改 route、权限决策或整体 `question_type`。
- 对每个 variant 执行现有 hybrid retrieval，合并去重后在 Evidence Pack 之前执行 deterministic rerank。
- rerank 只在 retrieval results 层选择最多 `SearchPlan.max_results` 条结果进入 Evidence Pack，不新增独立语义过滤阈值。
- 保持原始 query、path、symbol 和 exact token 命中的优先权；容量允许时不得被 variant-only 结果挤掉。
- rewrite/rerank audit 只进入内部 trace，不暴露完整 variants、完整文件内容、完整 Evidence Pack、本机绝对路径或新的 `/chat` 顶层字段。
- 同步 capability status：V12 后应说明 deterministic query rewrite/rerank 已实现，但真实 LLM rewrite/rerank、memory 和 context compression 仍未实现。

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `repo-query-understanding-rag`: 增加 deterministic query rewrite、multi-query retrieval merge、before-Evidence rerank 和相关 audit/fallback 规则。
- `agent-loop-tool-execution`: AgentLoop 在 repo_search 链路中记录 rewrite/rerank 内部 trace，并保持 permission、approval、ToolExecutor、Evidence Pack 和 grounded answer 边界。

## Impact

- Code: `app/rag/**`, `app/tools/tool_executor.py`, `app/harness/kernel.py`
- Tests: `tests/test_query_rewrite.py`, `tests/test_repo_rerank.py`, `tests/test_repo_rag.py`, `tests/test_agent_harness_kernel.py`, `tests/test_chat_api.py`
- Docs: `README.md`, `docs/ARCHITECTURE.md`, `docs/PROGRESS.md`, `docs/FEATURE_LIST.json`, `HANDOFF_TO_NEXT_CHAT.md`
- OpenSpec / Harness: `openspec/changes/v12-query-rewrite-rerank/**`, `openspec/specs/repo-query-understanding-rag/spec.md`, `openspec/specs/agent-loop-tool-execution/spec.md`, `.harness/allowed_files.md`, `.harness/review_checklist.md`
- Dependencies: none.
