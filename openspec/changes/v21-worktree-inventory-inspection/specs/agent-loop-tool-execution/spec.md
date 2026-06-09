## ADDED Requirements

### Requirement: Agent Loop Routes Worktree Inventory And Inspection As Strict Reads

系统 SHALL handle explicit worktree inventory and inspection intents before patch, verification, audit recovery, capability status, and repo-search fallback. These intents MUST NOT call repo RAG, verification, patch, cleanup, or any write tool.

Inspection SHALL emit `worktree_inspection` instead of the V20 `worktree_status` event. Inventory SHALL emit `worktree_inventory`.

#### Scenario: Worktree inspection replaces status event

- **WHEN** a user sends `worktree status <worktree_id>`
- **THEN** AgentLoop performs V21 inspection
- **AND** request-local trace contains `worktree_inspection`
- **AND** request-local trace does not contain `worktree_status`

### Requirement: Worktree Read Events Skip Persistent Audit

系统 SHALL preserve the unified `AgentLoop.run() -> _run_inner() -> _record_audit_and_return()` structure. `_skip_persistent_audit_for_result()` MUST skip persistent audit when a result contains `worktree_inventory` or `worktree_inspection`.

The request MAY retain safe in-memory trace events, but preview content MUST NOT enter those summaries.

#### Scenario: Existing audit database is unchanged

- **WHEN** inventory or inspection runs while an audit database already exists
- **THEN** the request returns its read-only answer
- **AND** no persistent audit row is added
