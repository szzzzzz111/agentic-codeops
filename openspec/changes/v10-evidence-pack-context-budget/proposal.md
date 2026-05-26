## Why

V9 已经能返回 hybrid repo RAG citation，但检索结果还只是直接进入 `/chat` 的简短证据文本，缺少可审计的证据包边界和后续模型上下文预算。V10 需要先把 retrieval output 变成稳定、可测试、可追踪的 Evidence Pack，再为 V11 的 grounded answer / model provider 边界准备输入约束。

## What Changes

- 新增 Evidence Pack：把 repo retrieval 结果整理为结构化 evidence items，保留相对路径、1-based 行号、score、snippet、来源摘要和稳定 evidence id。
- 新增 Context Budget：用确定性字符预算限制可进入后续回答上下文的 evidence snippets，并记录 included / omitted / truncated 摘要。
- 将 Evidence Pack 摘要接入现有内部 trace 和 `ToolExecutionResult.audit_summary`，但不新增 `/chat` 必需顶层字段。
- 保持 V9 hybrid retrieval、只读文件工具、权限/审批边界和 `ToolExecutor(repo_rag)` 执行入口。
- 明确不做 grounded answer、model provider、LLM prompt assembly、query rewrite、rerank、memory、context compression 或外部存储。

## Capabilities

### New Capabilities

- 无。

### Modified Capabilities

- `repo-query-understanding-rag`: 在现有 repo-local query understanding / hybrid retrieval 能力上增加 Evidence Pack 和 Context Budget 规范。

## Impact

- Code: `app/rag/evidence.py`, `app/rag/__init__.py`, `app/tools/tool_executor.py`, `app/harness/kernel.py`
- Tests: `tests/test_evidence_pack.py`, `tests/test_agent_harness_kernel.py`, `tests/test_chat_api.py`
- Docs: `README.md`, `docs/ARCHITECTURE.md`, `docs/PROGRESS.md`, `docs/FEATURE_LIST.json`, `HANDOFF_TO_NEXT_CHAT.md`
- OpenSpec / Harness: `openspec/changes/v10-evidence-pack-context-budget/**`, `.harness/allowed_files.md`, `.harness/review_checklist.md`
- API: `/chat` 顶层响应 contract 保持 `trace_id`、`answer`、`related_files`、`tool_calls`，不新增必需字段。
- Dependencies: 不新增外部运行时依赖、网络服务、模型下载或持久化存储。
