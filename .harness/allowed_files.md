# 当前 Harness 写入边界

当前活跃阶段：V10 `v10-evidence-pack-context-budget`（implementation）。

本阶段目标：在 V9 hybrid repo RAG 之上增加内部 Evidence Pack 和 deterministic character Context Budget 边界。用户已确认按 V10 plan 进入实现。

## 当前允许修改

- `openspec/changes/v10-evidence-pack-context-budget/proposal.md`
- `openspec/changes/v10-evidence-pack-context-budget/design.md`
- `openspec/changes/v10-evidence-pack-context-budget/tasks.md`
- `openspec/changes/v10-evidence-pack-context-budget/specs/repo-query-understanding-rag/spec.md`
- `openspec/specs/agent-loop-tool-execution/spec.md`
- `openspec/specs/README.md`
- `openspec/changes/README.md`
- `.harness/allowed_files.md`
- `.harness/review_checklist.md`
- `README.md`
- `docs/ARCHITECTURE.md`
- `docs/PROGRESS.md`
- `docs/FEATURE_LIST.json`
- `HANDOFF_TO_NEXT_CHAT.md`
- `app/rag/repo_rag.py`
- `app/rag/evidence.py`
- `app/rag/__init__.py`
- `app/tools/tool_executor.py`
- `app/harness/kernel.py`
- `tests/test_repo_rag.py`
- `tests/test_evidence_pack.py`
- `tests/test_agent_harness_kernel.py`
- `tests/test_chat_api.py`

## 禁止修改

- 不恢复旧 `specs/00x-*` 作为规格入口。
- 不把 OpenSpec、Superpowers、MCP、plugin 或参考项目写成 RepoPilot runtime 能力。
- 不新增 `/chat` 必需顶层字段；V10 Evidence Pack 只进入内部结构和 audit/trace 摘要。
- 不绕过 `ToolExecutor(repo_rag)`、`PermissionPolicy`、`ApprovalGate` 或安全文件工具边界。
- 不默认接入 Milvus、Elasticsearch、PgVector、Qdrant、真实外部 embedding 服务、模型下载、tokenizer 依赖或持久化向量索引。
- 不实现 grounded answer、model provider、LLM prompt assembly、query rewrite、rerank、memory、context compression、SandboxRunner、skill execution 或多 agent orchestration。
