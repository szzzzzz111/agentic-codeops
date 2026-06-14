# 当前 Harness 写入边界

当前活跃阶段：V22 Worktree Re-verification（实现完成，等待 review）。

V22 只开放现有 retained worktree 白名单验证重跑所需的最小实现、测试、规格与文档边界。

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
- `openspec/changes/v22-worktree-re-verification/**`
- `openspec/specs/agent-loop-tool-execution/spec.md`
- `openspec/specs/chat-api/spec.md`
- `openspec/specs/harness-development-workflow/spec.md`
- `openspec/specs/persistent-audit-recovery/spec.md`
- `openspec/specs/verification-runner/spec.md`
- `openspec/specs/worktree-isolation/spec.md`
- `openspec/specs/worktree-reverification/spec.md`
- `app/worktrees/**`
- `app/harness/kernel.py`
- `app/audit/manager.py`
- `app/tools/tool_executor.py`
- `app/verification/runner.py`
- `tests/test_worktree_reverification.py`
- `tests/test_worktree_inspection.py`
- `tests/test_worktree_isolation.py`
- `tests/test_verification_runner.py`
- `tests/test_agent_harness_kernel.py`
- `tests/test_chat_api.py`
- `tests/test_persistent_audit.py`

## 禁止修改 / 禁止行为

- 不恢复旧 `specs/00x-*` 作为规格入口。
- 不把 OpenSpec、Superpowers、MCP、plugin 或 `.codex/skills/**` 写成 RepoPilot runtime 能力。
- 不新增 `/chat` 顶层字段，不新增公开 audit/status/tasks/verification/worktree API。
- 不修改 `app/patching/**`；re-verification 不读取、修改或重新应用 patch。
- 不改变现有 Verification Runner 白名单，不接受用户附加参数、路径、环境变量、管道、重定向或任意 shell。
- 不执行 cleanup、discard、unlock/remove、reconciliation、promotion、commit、merge 或 push。
- 不执行后台任务、subagents、connectors 或前端工作。
- 不公开或持久化完整 stdout/stderr、绝对路径、`.git` 路径、DB 路径、环境变量、API key、secret、raw Git 输出、diff 或 preview。
- 不因一致性失败自动修复、重试、创建未知 worktree 或修改主工作区。
