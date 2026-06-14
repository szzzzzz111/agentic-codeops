## Why

V20 creates retained isolated worktrees and V21 safely inspects them, but users cannot explicitly rerun an approved verification command inside an existing retained worktree. V22 adds that narrow controlled action while preserving scope isolation, worktree consistency, patch state, audit safety, and the existing `/chat` contract.

## What Changes

- Add explicit `worktree verify <worktree_id> <command_label>` and `重新验证 worktree <worktree_id> <command_label>` commands.
- Validate current `user_id + repo_key`, expected directory, Git registry membership/path, and worktree HEAD/base consistency before execution.
- Reuse the existing Verification Runner whitelist, Harness approval chain, timeout, output limits, and redaction.
- Run verification only inside the retained worktree and update only existing worktree verification lifecycle fields.
- Record every re-verification request as a redacted scoped persistent audit result distinguishable from initial/standalone verification.
- Keep the related patch `applied_in_worktree`, keep `/chat` top-level fields unchanged, and explicitly exclude cleanup, reconciliation, promotion, patch mutation, main-workspace mutation, commit, merge, and push.

## Capabilities

### New Capabilities

- `worktree-reverification`: Explicit fail-closed re-verification of an existing retained worktree.

### Modified Capabilities

- `worktree-isolation`: Retained worktrees may be explicitly re-verified without changing patch state.
- `verification-runner`: Existing labels and execution protections apply to retained worktree re-verification.
- `agent-loop-tool-execution`: Route strict re-verification intent before standalone verification and excluded fallbacks.
- `persistent-audit-recovery`: Persist one redacted, worktree-related audit result for every re-verification request.
- `chat-api`: Return re-verification summaries through the existing response contract.
- `harness-development-workflow`: Require planning, safety evidence, and an implementation confirmation gate for V22.

## Impact

- Code: targeted `app/worktrees/**`, Kernel routing/audit mapping, and existing verification/tool boundaries only where required.
- Tests: new V22 re-verification tests plus targeted AgentLoop, API, audit, V20, and V21 regressions.
- Docs: V22 OpenSpec artifacts, harness boundaries, durable stage docs, and feature list.
- Dependencies: no new external dependency.
