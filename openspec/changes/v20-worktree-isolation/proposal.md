## Why

V16-V19 already let RepoPilot propose patches, apply confirmed patches, run whitelisted verification, and persist redacted audit. The remaining safety gap is that RepoPilot-owned code mutation still lands directly in the user's main working tree.

V20 closes that gap by isolating standalone patch apply and combined Patch + Verify inside a retained repo-local worktree. This keeps the user's workspace stable while preserving the existing `/chat` contract and the current standalone verification workflow.

## What Changes

- Add a new `worktree-isolation` capability with repo-local worktree lifecycle management and state storage.
- Add approval-gated `worktree_create` before standalone patch apply and combined Patch + Verify.
- Route `patch_apply` and combined `verification_run` through an internal `execution_repo_path`.
- Add read-only `worktree status <worktree_id>` queries through existing `/chat.answer`.
- Persist redacted worktree lifecycle summaries and integrate them with persistent audit.
- Keep standalone verification on the main working tree.
- Keep `/chat` top-level response schema unchanged.

## Capabilities

### New Capabilities

- `worktree-isolation`

### Modified Capabilities

- `agent-loop-tool-execution`
- `chat-api`
- `safe-patch-authoring`
- `patch-verify-loop`
- `verification-runner`
- `persistent-audit-recovery`
- `harness-development-workflow`

## Impact

- Code: `app/worktrees/**`, targeted Kernel / ToolExecutor / patch / audit hooks.
- Tests: new worktree tests plus targeted AgentLoop / chat API / patch / audit updates.
- Docs: harness files, durable docs, V20 change artifacts, and long-term specs.

## Non-Goals

- No worktree list, delete, prune, merge, commit, push, replay, rerun, or retry commands.
- No copying uncommitted main-worktree changes into isolated worktrees.
- No arbitrary Git or shell execution.
