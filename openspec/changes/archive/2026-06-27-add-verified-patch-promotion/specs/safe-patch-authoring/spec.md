## ADDED Requirements

### Requirement: Verified Promotion Uses A Promoted Patch Terminal State

系统 SHALL use patch status `promoted` only after a verified retained worktree promotion has successfully updated the main workspace and the promotion state machine can truthfully record success.

Only a scoped promotion flow MAY transition a patch from `applied_in_worktree` to `promoted`. Ordinary patch confirmation MUST NOT apply an `applied_in_worktree` patch to the main workspace unless a complete promotion preflight and promotion-specific approval context exists.

#### Scenario: Promotion succeeds after isolated verification

- **WHEN** a scoped patch in `applied_in_worktree` passes all promotion checks and the main workspace write succeeds
- **THEN** the patch transitions to `promoted`
- **AND** the transition does not imply commit, merge, push, branch creation, PR creation, or worktree deletion
