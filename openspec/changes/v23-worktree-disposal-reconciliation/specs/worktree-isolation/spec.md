## ADDED Requirements

### Requirement: Retained Worktrees Have Explicit Disposal Terminal States

系统 SHALL use `disposal_failed` to represent a partially completed disposal requiring explicit reconciliation and `discarded` to represent confirmed worktree cleanup terminal state.

Eligible retained worktrees MAY transition to these states only through V23 confirmed disposal/reconciliation. A disposed worktree MUST NOT be treated as eligible for inspection-derived execution, re-verification, patch mutation, or promotion.

#### Scenario: Disposed worktree is terminal

- **WHEN** a worktree reaches `discarded`
- **THEN** repeated disposal/reconciliation is idempotent
- **AND** re-verification MUST reject the worktree
