## ADDED Requirements

### Requirement: Retained Worktrees May Be Re-verified Without Patch Mutation

系统 SHALL allow an existing scoped retained worktree to be explicitly re-verified after fail-closed consistency preflight.

Executed success SHALL use `verification_succeeded`; executed non-success SHALL use `verification_failed`. Preflight or approval failure MUST preserve the previous lifecycle. The associated patch MUST remain `applied_in_worktree` in all cases, and no `verification_rerun_*` lifecycle SHALL be added.

#### Scenario: Preflight failure preserves retained state

- **WHEN** a retained worktree fails consistency preflight
- **THEN** verification does not run
- **AND** the previous worktree lifecycle and patch state remain unchanged
