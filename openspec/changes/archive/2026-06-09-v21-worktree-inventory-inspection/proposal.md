## Why

V20 retains isolated worktrees but exposes only a narrow per-id status summary. V21 adds safe, scoped visibility so an operator can understand retained worktree state before any later re-verification, disposal, reconciliation, or promotion stage.

## What Changes

- Add read-only `worktree list` / `列出 worktree` inventory for the current `user_id + repo_key` scope.
- Upgrade V20 `worktree status <worktree_id>` / `查看 worktree <worktree_id>` into detailed V21 inspection.
- Return lifecycle metadata, tracked changed files, diffstat, hunk count, verification summary, consistency checks, and bounded redacted preview through `/chat.answer`.
- Require preview paths to come only from machine-readable fixed Git output, and report untracked files by count only.
- Skip persistent audit for inventory / inspection so reads never create or modify `.repopilot/`, databases, or repository state.
- Keep `/chat` top-level contract unchanged and explicitly exclude all V22-V24 write behavior.

## Capabilities

### New Capabilities

- `worktree-inspection`: Scoped read-only inventory, consistency inspection, and bounded safe preview.

### Modified Capabilities

- `worktree-isolation`: V21 inspection replaces the V20 narrow status query.
- `agent-loop-tool-execution`: Add deterministic inventory / inspection routing and persistent-audit skip events.
- `chat-api`: Return inventory / inspection only through the existing answer contract.
- `persistent-audit-recovery`: Inventory / inspection must not persist audit events because they are strict no-state-mutation reads.
- `harness-development-workflow`: Require planning, safety evidence, and an implementation confirmation gate for V21.

## Impact

- Code: targeted `app/worktrees/**`, Kernel routing/audit skip, and shared safe-file checks.
- Tests: new V21 inspection tests plus targeted AgentLoop, API, audit, and V20 compatibility updates.
- Docs: V21 OpenSpec artifacts, harness boundaries, durable stage docs, and feature list.
- Dependencies: no new external dependency; fixed Git argv and stdlib SQLite only.
