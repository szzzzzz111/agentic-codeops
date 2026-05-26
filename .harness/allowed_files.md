# 当前 Harness 写入边界

当前活跃阶段：无。V10 `v10-evidence-pack-context-budget` 已实现、提交并归档。

下一阶段开始前，需要先创建新的 OpenSpec change，并重新同步本文件与 `.harness/review_checklist.md`。

## 当前允许修改

- `openspec/changes/archive/2026-05-26-v10-evidence-pack-context-budget/**`
- `openspec/specs/repo-query-understanding-rag/spec.md`
- `.harness/allowed_files.md`
- `.harness/review_checklist.md`
- `docs/PROGRESS.md`
- `HANDOFF_TO_NEXT_CHAT.md`

## 禁止修改

- 不恢复旧 `specs/00x-*` 作为规格入口。
- 不把 OpenSpec、Superpowers、MCP、plugin 或参考项目写成 RepoPilot runtime 能力。
- 不新增 `/chat` 必需顶层字段；V10 Evidence Pack 只进入内部结构和 audit/trace 摘要。
- 不绕过 `ToolExecutor(repo_rag)`、`PermissionPolicy`、`ApprovalGate` 或安全文件工具边界。
- 不默认接入 Milvus、Elasticsearch、PgVector、Qdrant、真实外部 embedding 服务、模型下载、tokenizer 依赖或持久化向量索引。
- 不实现 grounded answer、model provider、LLM prompt assembly、query rewrite、rerank、memory、context compression、SandboxRunner、skill execution 或多 agent orchestration。
