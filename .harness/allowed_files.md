# 当前 Harness 写入边界

当前 active development stage 为 V23 Worktree Disposal / Reconciliation closeout。runtime/tests 已按明确确认实现。

## 当前允许修改

- `openspec/changes/v23-worktree-disposal-reconciliation/**`
- `.harness/allowed_files.md`
- `.harness/review_checklist.md`
- `README.md`
- `docs/ARCHITECTURE.md`
- `docs/PROGRESS.md`
- `docs/FEATURE_LIST.json`
- `HANDOFF_TO_NEXT_CHAT.md`

## 已确认实现范围

- `app/worktrees/**`
- `app/patching/store.py`
- `app/harness/kernel.py`
- `app/patching/types.py`
- `app/tools/tool_executor.py`
- `app/audit/manager.py`
- `tests/test_worktree_disposal.py`
- `tests/test_worktree_inventory.py`
- `tests/test_worktree_reverification.py`
- `tests/test_worktree_isolation.py`
- `tests/test_patch_authoring.py`
- `tests/test_agent_harness_kernel.py`
- `tests/test_chat_api.py`
- `tests/test_persistent_audit.py`
- `scripts/check_stage_docs.ps1`
- `openspec/specs/worktree-disposal-reconciliation/spec.md`
- `openspec/specs/worktree-isolation/spec.md`
- `openspec/specs/worktree-inspection/spec.md`
- `openspec/specs/worktree-reverification/spec.md`
- `openspec/specs/safe-patch-authoring/spec.md`
- `openspec/specs/agent-loop-tool-execution/spec.md`
- `openspec/specs/persistent-audit-recovery/spec.md`
- `openspec/specs/chat-api/spec.md`
- `openspec/specs/harness-development-workflow/spec.md`

## 禁止修改 / 禁止行为

- runtime 或 tests 修改必须保持在 V23 已确认范围。
- 不得执行 patch promotion、patch reapply/mutation、commit、merge、push、隐式 reconciliation、自动修复或自动重试。
- 不得使用 `git worktree prune`，不得清理未知、跨 scope、未明确确认或无法证明 linked-worktree ownership 的目录。
- 不得新增公开 REST API、`/chat` 顶层字段、任意 shell、后台任务、subagents、connectors 或前端。
- 不得把 OpenSpec、Superpowers、MCP、plugin 或 `.codex/skills/**` 写成 RepoPilot runtime 能力。
