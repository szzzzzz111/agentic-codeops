## ADDED Requirements

### Requirement: Disposal Rejects Promoted Worktrees In V25

系统 SHALL reject V23 disposal/reconciliation for `promoted` worktrees in V25 because promoted patch closeout is distinct from `applied_in_worktree` discard closeout.

Promotion MUST NOT delete the retained worktree. Explicit cleanup of promoted retained worktrees requires a future scoped lifecycle contract.

#### Scenario: Promoted worktree is not discarded by V23

- **WHEN** a user requests discard or reconciliation for a scoped `promoted` worktree
- **THEN** V23 disposal/reconciliation rejects the request
- **AND** it MUST NOT delete the retained worktree or mark the promoted patch `discarded`
