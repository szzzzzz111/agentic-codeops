## ADDED Requirements

### Requirement: Agent Loop Routes Verified Patch Promotion Before Re-verification

系统 SHALL handle recognized Verified Patch Promotion requests after worktree disposal/reconciliation and before retained worktree re-verification, patch handling, standalone verification, audit recovery, capability status, and repo-search fallback.

The route MUST intercept malformed promotion-like requests, MUST NOT call repo RAG, re-verification, patch apply, disposal, commit, merge, push, branch, PR, or prune behavior unless the exact promotion preflight and approval path succeeds.

#### Scenario: Promotion-like request cannot fall through

- **WHEN** a user sends a malformed promotion-like request for a worktree id
- **THEN** AgentLoop rejects it in the promotion route
- **AND** it MUST NOT run V22 re-verification or any later route

### Requirement: Verified Patch Promotion Uses A Distinct Permission Context

系统 SHALL require a promotion-specific `ToolInvocationContext` or equivalent normalized operation kind before approval-gated main-workspace `patch_apply` can run for promotion.

The context MUST be produced only after scoped promotion preflight validates worktree lifecycle, patch status, base commit, main workspace cleanliness, Git/worktree metadata consistency, and stored patch content integrity. Existing direct patch confirmation MUST remain limited to its existing eligible pending-patch flow.

#### Scenario: Applied-in-worktree patch does not bypass approval

- **WHEN** a caller tries to apply an `applied_in_worktree` patch without promotion preflight context
- **THEN** `PermissionPolicy` / `ApprovalGate` rejects execution
- **AND** `ToolExecutor.patch_apply` is not called
