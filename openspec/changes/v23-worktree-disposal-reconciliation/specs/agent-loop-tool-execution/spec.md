## ADDED Requirements

### Requirement: Agent Loop Routes Confirmed Disposal Before Re-verification

系统 SHALL handle worktree disposal/reconciliation after worktree inventory/inspection and before worktree re-verification, patch handling, standalone verification, audit recovery, capability status, and repo-search fallback.

The route MUST intercept malformed disposal-like requests, MUST NOT call repo RAG, patch apply/reapply, verification, promotion, commit, merge, push, or prune, and MAY call only the approved `worktree_dispose` tool after successful preflight.

#### Scenario: Disposal-like request cannot fall through

- **WHEN** a user sends `discard worktree <worktree_id>` without confirmation
- **THEN** AgentLoop rejects it in the V23 route
- **AND** it MUST NOT run V22 re-verification or any later route

### Requirement: Worktree Disposal Uses The Existing Harness Boundary

系统 SHALL register `worktree_dispose` as `read_only=False`, `risk="write"`, and `requires_approval=True`.

Accepted disposal MUST pass through `ToolRegistry`, `PermissionPolicy`, `ApprovalGate`, and `ToolExecutor`. User input MUST NOT provide Git argv, path, cwd, environment, timeout, or reconciliation steps.

#### Scenario: Missing valid context blocks disposal

- **WHEN** `worktree_dispose` lacks a valid confirmed scoped context
- **THEN** permission/approval rejects execution
- **AND** no Git, filesystem, or store mutation occurs
