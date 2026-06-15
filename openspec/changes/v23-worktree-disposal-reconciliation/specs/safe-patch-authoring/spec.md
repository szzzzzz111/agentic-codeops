## ADDED Requirements

### Requirement: Worktree Disposal Uses Scoped Patch Terminal Updates

系统 SHALL provide a true no-create existing patch-store lookup and a scoped patch status update qualified by `patch_id + user_id + repo_key`.

V23 disposal/reconciliation MUST use the scoped update to transition an associated `applied_in_worktree` patch to `discarded` only after worktree cleanup and worktree metadata closeout succeed. The legacy unscoped `mark_status` method SHALL remain available for compatibility and MUST NOT be used by V23.

#### Scenario: Missing patch store is not created during preflight

- **WHEN** V23 checks a repo without an existing patch database
- **THEN** it returns a safe failure
- **AND** it MUST NOT create `.repopilot` or the patch database
