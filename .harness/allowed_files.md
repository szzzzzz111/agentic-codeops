# 当前 Harness 写入边界

当前活跃阶段：无。

V18 Patch + Verify Loop 已归档到 `openspec/changes/archive/2026-06-04-v18-patch-verify-loop/`。下一阶段开始前必须先创建新的 OpenSpec change，并同步本文件和 `.harness/review_checklist.md`。

## 当前允许修改

- `.harness/allowed_files.md`
- `.harness/review_checklist.md`
- `README.md`
- `docs/ARCHITECTURE.md`
- `docs/PROGRESS.md`
- `docs/FEATURE_LIST.json`
- `HANDOFF_TO_NEXT_CHAT.md`

## 禁止修改

- 未创建并验证新阶段 OpenSpec change 前，不得开始新的运行时代码实现。
- 不恢复旧 `specs/00x-*` 作为规格入口。
- 不把 OpenSpec、Superpowers、MCP、plugin 或参考项目写成 RepoPilot runtime 能力。
- 不绕过 `ToolExecutor(repo_rag / patch_apply / verification_run)`、`PermissionPolicy`、`ApprovalGate` 或安全文件工具边界。
- 不新增 `/chat` 顶层字段，不新增公开 `/patches`、`/status`、`/tasks` 或 `/verification` API。
- 不开放任意 shell 命令、用户自定义验证参数、targeted pytest、管道、重定向、环境变量注入或 `ruff --fix`。
- 不让 API handler、AgentLoop parser 或 patch parser 直接调用 subprocess；验证执行只能通过 `ToolExecutor.verification_run(...)`。
- 不把完整 diff 文本、完整 Evidence Pack、完整 provider prompt/output、本机绝对路径、DB 路径或 API key 暴露到公开响应。
- 不把完整 stdout、完整 stderr、完整 internal trace、环境变量或本机绝对路径暴露到公开验证响应。
- 不默认接入 Milvus、Elasticsearch、PgVector、Qdrant、真实外部 embedding 服务、模型下载、tokenizer 依赖或持久化向量索引。
- 不把真实 LLM rewrite/rerank、向量 memory、自动 memory 总结、context compression、SandboxRunner、skill execution、后台任务、自动循环执行、真实 subagent orchestration、Persistent Audit / Recovery 或 worktree automation 写成已实现。
- 当前无 active stage；不得继续扩展 V18 runtime，V19 前不得持久化 verification result、patch attempt 或 task event，不得创建 worktree，不得自动 commit/push。
- 不让默认验证依赖真实网络、真实 API key 或真实模型输出。
