## Why

RepoPilot retains isolated worktrees after patch execution so users can inspect and re-verify them, but it currently has no explicit safe way to dispose them or reconcile a partially completed disposal. V23 adds that lifecycle closeout while preventing unknown-directory deletion, cross-scope mutation, implicit repair, and sensitive audit leakage.

## What Changes

- Add exact confirmed discard and reconcile commands for the current `user_id + repo_key` worktree scope.
- Add fail-closed disposal/reconciliation preflight, controlled Git/directory/metadata/patch ordering, idempotent terminal states, and redacted persistent attempt audit.
- Treat the shared Git metadata runner timeout and pre-read output hard limit as blocking V23 work.
- Add a true no-create existing patch-store lookup and scoped patch status update while retaining the legacy unscoped method for compatibility.
- Keep `/chat` top-level fields unchanged and exclude promotion, patch mutation, commit, merge, push, implicit repair, automatic retry, arbitrary shell, background tasks, subagents, connectors, and frontend behavior.

## Capabilities

### New Capabilities

- `worktree-disposal-reconciliation`: Explicit fail-closed disposal and narrow reconciliation of scoped retained worktrees.

### Modified Capabilities

- `worktree-isolation`: Add disposal terminal states and safe lifecycle closeout.
- `worktree-inspection`: Share hardened bounded Git metadata execution.
- `worktree-reverification`: Share hardened bounded Git metadata execution and reject disposed states.
- `safe-patch-authoring`: Add scoped `discarded` patch transition and no-create existing-store access.
- `agent-loop-tool-execution`: Route V23 before V22 and execute disposal through the Harness boundary.
- `persistent-audit-recovery`: Persist one redacted disposal/reconciliation event per recognized attempt.
- `chat-api`: Return V23 results through the existing contract.
- `harness-development-workflow`: Require planning review and implementation confirmation before runtime/test edits.

## Impact

- Code: targeted `app/worktrees/**`, patch store, Kernel/tool/audit boundaries, and no other runtime surface.
- Tests: new V23 disposal tests plus focused V20-V22, patch-store, AgentLoop, API, and audit regressions.
- Docs: V23 OpenSpec artifacts, harness boundaries, feature list, progress, handoff, and implementation-time durable docs.
- Dependencies: no new external dependency.
