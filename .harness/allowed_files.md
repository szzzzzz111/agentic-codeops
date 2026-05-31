# 当前 Harness 写入边界

当前活跃阶段：无。

V16 Safe Patch Authoring 已实现并归档到 `openspec/changes/archive/2026-05-31-v16-safe-patch-authoring/`。下一阶段开始前，必须先创建新的 OpenSpec change，并同步更新本文件和 `.harness/review_checklist.md`。

## 当前允许修改

- `docs/PROGRESS.md`（仅限阶段收尾、交接或状态修正）
- `HANDOFF_TO_NEXT_CHAT.md`（仅限阶段收尾、交接或状态修正）
- `.harness/allowed_files.md`（仅限阶段收尾、交接或下一阶段规划）
- `.harness/review_checklist.md`（仅限阶段收尾、交接或下一阶段规划）
- `README.md`（仅限阶段收尾、交接或状态修正）
- `docs/ARCHITECTURE.md`（仅限阶段收尾、交接或状态修正）
- `docs/FEATURE_LIST.json`（仅限阶段收尾、交接或状态修正）
- `tests/test_chat_api.py`（仅限 archive 后文档路线图断言同步）
- `openspec/specs/**`（仅限 archive 后长期 spec 同步修正）
- `openspec/changes/archive/**`（仅限 archive 后记录修正）

## 禁止修改

- 未创建并验证下一阶段 OpenSpec change 前，不得开始新的运行时代码实现。
- 不恢复旧 `specs/00x-*` 作为规格入口。
- 不把 OpenSpec、Superpowers、MCP、plugin 或参考项目写成 RepoPilot runtime 能力。
- 不绕过 `ToolExecutor(repo_rag)`、`PermissionPolicy`、`ApprovalGate` 或安全文件工具边界。
- 不新增 `/chat` 顶层字段，不新增公开 `/patches`、`/status` 或 `/tasks` API。
- 不把完整 diff 文本、完整 Evidence Pack、完整 provider prompt/output、本机绝对路径、DB 路径或 API key 暴露到公开响应。
- 不默认接入 Milvus、Elasticsearch、PgVector、Qdrant、真实外部 embedding 服务、模型下载、tokenizer 依赖或持久化向量索引。
- 后续不得把真实 LLM rewrite/rerank、向量 memory、自动 memory 总结、context compression、SandboxRunner、skill execution、后台任务、自动循环执行、真实 subagent orchestration 或 worktree automation 写成已实现，除非新阶段明确开放。
- 不让默认验证依赖真实网络、真实 API key 或真实模型输出。
