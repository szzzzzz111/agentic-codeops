## ADDED Requirements

### Requirement: Worktree Creation Uses The Existing Harness Boundary

系统 SHALL register a `worktree_create` execution tool for V20. `worktree_create` MUST pass through `ToolRegistry`, `PermissionPolicy`, `ApprovalGate`, and `ToolExecutor`, and MUST NOT be called directly from API handlers or free-form parsers.

Standalone patch apply and combined Patch + Verify MUST create a worktree first, then pass an internal `execution_repo_path` to `patch_apply` and combined `verification_run`. This execution path MUST NOT enter `/chat` top-level fields, `tool_calls`, or persistent audit payloads.

#### Scenario: Patch confirm uses isolated execution path

- **WHEN** a confirmed patch apply request passes worktree preconditions
- **THEN** AgentLoop first calls `worktree_create`
- **AND** `patch_apply` runs against the worktree execution repo path rather than the main repo path
