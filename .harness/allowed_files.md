# 当前 Harness 写入边界

当前活跃阶段：无 active implementation stage。

V19 Persistent Audit / Recovery 已实现、通过 external review、归档到 `openspec/changes/archive/2026-06-05-v19-persistent-audit-recovery/`，并 fast-forward 合并推送；post-merge handoff 收尾后 `main` 与 `agentic-codeops/main` 指向 `633560f5d6020f70897494ee216ad016ccf66328`。下一阶段开始前必须重新同步本文件和 `.harness/review_checklist.md`。

## 当前允许修改

- `.harness/allowed_files.md`
- `.harness/review_checklist.md`
- `README.md`
- `docs/ARCHITECTURE.md`
- `docs/PROGRESS.md`
- `docs/FEATURE_LIST.json`
- `HANDOFF_TO_NEXT_CHAT.md`
- `docs/FEATURE_LIST.json`

上述路径仅用于 post-merge handoff 文档修正。V20 或其他新阶段开始前必须替换为该阶段自己的 allowed files。

## 可选流程文档修改

以下路径只允许用于 Stage Debt Sweep / handoff 流程纪律修复；不得作为 RepoPilot runtime capability：

- `.codex/skills/repo-stage-review-loop/SKILL.md`
- `.codex/skills/repo-stage-handoff/SKILL.md`

## 禁止修改 / 禁止行为

- 不恢复旧 `specs/00x-*` 作为规格入口。
- 不把 OpenSpec、Superpowers、MCP、plugin、`.codex/skills/**` 或参考项目写成 RepoPilot runtime 能力。
- 不绕过 `ToolExecutor(repo_rag / patch_apply / verification_run)`、`PermissionPolicy`、`ApprovalGate` 或安全文件工具边界。
- 不新增 `/chat` 顶层字段，不新增公开 audit/status/tasks/verification API。
- 不开放任意 shell 命令、用户自定义验证参数、targeted pytest、管道、重定向、环境变量注入或 `ruff --fix`。
- 不让 API handler、AgentLoop parser、patch parser 或 audit/recovery intent 直接调用 subprocess。
- 不把完整 diff、完整 stdout/stderr、完整 Evidence Pack、完整 provider prompt/output、完整 internal trace、本机绝对路径、DB 路径、环境变量、API key 或 secret 持久化或暴露到公开响应。
- 不默认接入 Milvus、Elasticsearch、PgVector、Qdrant、真实外部 embedding 服务、模型下载、tokenizer 依赖或持久化向量索引。
- 不实现 V20 Worktree Isolation，不创建 worktree。
- 不实现真实 subagents、connectors、notifications、heartbeat/cron 或 always-on assistant。
- 不自动 replay、rerun、reapply、resume、commit、push 或根据失败自动生成修复 patch。
- 不实现自动 retention/pruning；V19 audit 记录无限保留，查询默认最近 20 条。
- 不让默认验证依赖真实网络、真实 API key 或真实模型输出。
