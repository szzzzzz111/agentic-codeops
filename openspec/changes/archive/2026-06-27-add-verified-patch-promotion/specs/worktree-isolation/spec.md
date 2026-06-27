## ADDED Requirements

### Requirement: Verified Promotion Uses A Promoted Worktree Terminal State

系统 SHALL use worktree lifecycle `promoted` only after a scoped retained worktree with lifecycle `verification_succeeded` has been safely promoted to the main workspace through the Verified Patch Promotion flow.

`promoted` worktrees MUST remain retained and MUST NOT be deleted by promotion. In V25, `promoted` worktrees are terminal for re-verification, re-promotion, patch mutation, and disposal/reconciliation. Explicit cleanup of promoted retained worktrees requires a future scoped lifecycle change.

#### Scenario: Promoted worktree is terminal for V25 execution routes

- **WHEN** a worktree reaches `promoted`
- **THEN** promotion MUST NOT delete the retained worktree
- **AND** re-verification, re-promotion, patch mutation, and V23 disposal MUST reject it in V25
