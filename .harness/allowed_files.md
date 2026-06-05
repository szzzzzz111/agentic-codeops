# 当前 Harness 写入边界

当前活跃阶段：V19 Persistent Audit / Recovery。

V18 Patch + Verify Loop 及 V18 post-merge/handoff debt remediation 已 fast-forward 合并到 `main` 并推送到 `agentic-codeops/main`；当前 V19 基线为 `main` commit `8b93330`。V19 必须聚焦持久审计与只读恢复，不得把 V20 Worktree Isolation、真实 subagents/connectors/notifications/always-on assistant 或流程 skill 写成 runtime 能力。

## 当前允许修改

- `.harness/allowed_files.md`
- `.harness/review_checklist.md`
- `README.md`
- `docs/ARCHITECTURE.md`
- `docs/PROGRESS.md`
- `docs/FEATURE_LIST.json`
- `HANDOFF_TO_NEXT_CHAT.md`
- `openspec/changes/v19-persistent-audit-recovery/**`
- `openspec/specs/persistent-audit-recovery/spec.md`
- `openspec/specs/agent-loop-tool-execution/spec.md`
- `openspec/specs/chat-api/spec.md`
- `openspec/specs/safe-patch-authoring/spec.md`
- `openspec/specs/verification-runner/spec.md`
- `openspec/specs/long-task-agent-execution/spec.md`
- `openspec/specs/harness-development-workflow/spec.md`
- `app/audit/**`
- `app/harness/kernel.py`
- `app/tools/tool_executor.py`
- `app/verification/**`
- `app/patching/**`
- `app/longtask/**`
- `tests/test_persistent_audit.py`
- `tests/test_agent_harness_kernel.py`
- `tests/test_chat_api.py`
- `tests/test_patch_authoring.py`
- `tests/test_verification_runner.py`
- `tests/test_long_task.py`
- `scripts/check_stage_docs.ps1`
- `scripts/check_stage_closeout.ps1`

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
