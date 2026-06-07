# 当前 Harness 写入边界

当前活跃阶段：`V20 Worktree Isolation`

V20 目标是在不改变 `/chat` 顶层 contract 的前提下，把 RepoPilot 产生的单独 patch apply 与组合 Patch + Verify 放入受控 worktree 执行；独立 verification 继续保持当前工作区语义。

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
- `openspec/changes/v20-worktree-isolation/**`
- `openspec/specs/agent-loop-tool-execution/spec.md`
- `openspec/specs/chat-api/spec.md`
- `openspec/specs/harness-development-workflow/spec.md`
- `openspec/specs/patch-verify-loop/spec.md`
- `openspec/specs/persistent-audit-recovery/spec.md`
- `openspec/specs/safe-patch-authoring/spec.md`
- `openspec/specs/verification-runner/spec.md`
- `openspec/specs/worktree-isolation/spec.md`
- `app/harness/kernel.py`
- `app/tools/tool_executor.py`
- `app/patching/manager.py`
- `app/patching/store.py`
- `app/patching/types.py`
- `app/audit/manager.py`
- `app/audit/store.py`
- `app/worktrees/**`
- `tests/test_agent_harness_kernel.py`
- `tests/test_patch_authoring.py`
- `tests/test_persistent_audit.py`
- `tests/test_chat_api.py`
- `tests/test_worktree_isolation.py`

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
