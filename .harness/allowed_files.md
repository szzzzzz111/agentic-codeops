# 当前 Harness 写入边界

当前活跃阶段：无 active implementation stage。

V20 Worktree Isolation 已实现并归档。以下路径仅用于 archive 后验证与 handoff
收尾；下一阶段开始前必须重新同步本文件和 `.harness/review_checklist.md`。

## 当前允许修改

- `.harness/allowed_files.md`
- `.harness/review_checklist.md`
- `.harness/test_commands.md`
- `README.md`
- `docs/ARCHITECTURE.md`
- `docs/PROGRESS.md`
- `docs/FEATURE_LIST.json`
- `HANDOFF_TO_NEXT_CHAT.md`
- `scripts/check_stage_docs.ps1`
- `scripts/check_stage_closeout.ps1`
- `scripts/verify.ps1`
- `openspec/changes/archive/2026-06-07-v20-worktree-isolation/**`
- `openspec/specs/agent-loop-tool-execution/spec.md`
- `openspec/specs/chat-api/spec.md`
- `openspec/specs/harness-development-workflow/spec.md`
- `openspec/specs/patch-verify-loop/spec.md`
- `openspec/specs/persistent-audit-recovery/spec.md`
- `openspec/specs/safe-patch-authoring/spec.md`
- `openspec/specs/verification-runner/spec.md`
- `openspec/specs/worktree-isolation/spec.md`
- `tests/test_chat_api.py`

## 禁止修改 / 禁止行为

- 不恢复旧 `specs/00x-*` 作为规格入口。
- 不把 OpenSpec、Superpowers、MCP、plugin、`.codex/skills/**` 写成 RepoPilot runtime 能力。
- 不新增 `/chat` 顶层字段，不新增公开 audit/status/tasks/verification/worktree API。
- 不开放任意 shell 或用户自定义 Git / verification 参数。
- 不让 API handler、AgentLoop parser 或 patch parser 直接调 subprocess；Git / worktree 操作必须经受控工具与统一执行边界。
- 不绕过 `ToolExecutor`、`PermissionPolicy`、`ApprovalGate`、安全文件工具边界。
- 不实现 worktree 列表、清理、删除、merge、commit、push、replay、rerun、resume、自动修复或后台任务。
- 不把完整 diff、完整 stdout/stderr、绝对路径、`.git` 路径、DB 路径、环境变量、API key 或 secret 持久化或暴露到公开响应。
- 不默认接入真实 LLM、外部 embedding 服务、Milvus、Elasticsearch、PgVector、Qdrant 或持久化向量索引。
