# 当前 Harness 写入边界

当前活跃阶段：V21 Worktree Inventory / Inspection（external review 完成，等待 commit 确认）。

V21 只开放 worktree 只读 inventory / inspection 所需的最小实现、测试、规格与文档边界。

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
- `openspec/changes/v21-worktree-inventory-inspection/**`
- `openspec/specs/agent-loop-tool-execution/spec.md`
- `openspec/specs/chat-api/spec.md`
- `openspec/specs/harness-development-workflow/spec.md`
- `openspec/specs/persistent-audit-recovery/spec.md`
- `openspec/specs/worktree-inspection/spec.md`
- `openspec/specs/worktree-isolation/spec.md`
- `app/worktrees/**`
- `app/harness/kernel.py`
- `app/audit/manager.py`
- `app/tools/file_tools.py`
- `tests/test_worktree_inspection.py`
- `tests/test_worktree_isolation.py`
- `tests/test_agent_harness_kernel.py`
- `tests/test_chat_api.py`
- `tests/test_persistent_audit.py`

## 禁止修改 / 禁止行为

- 不恢复旧 `specs/00x-*` 作为规格入口。
- 不把 OpenSpec、Superpowers、MCP、plugin 或 `.codex/skills/**` 写成 RepoPilot runtime 能力。
- 不新增 `/chat` 顶层字段，不新增公开 audit/status/tasks/verification/worktree API。
- 不接受用户输入作为 per-file Git diff 路径；preview 路径只能来自固定 Git argv 的机器可解析输出。
- 不执行 re-verification、cleanup、discard、unlock/remove、reconciliation、promotion、commit、merge 或 push。
- 不执行任意 shell、后台任务、subagents、connectors 或前端工作。
- 不公开或持久化 raw diff、完整 stdout/stderr、绝对路径、`.git` 路径、DB 路径、环境变量、API key 或 secret。
