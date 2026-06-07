## ADDED Requirements

### Requirement: Combined Verification Can Run Inside A Worktree

V20 SHALL allow the combined Patch + Verify flow to run white-listed verification inside the isolated worktree execution repo path created for that request.

Standalone verification MUST keep the existing request repo path behavior. Verification running inside a worktree MUST NOT depend on pre-existing `.repopilot` state within that worktree checkout.

#### Scenario: Worktree verification does not require worktree-local state DBs

- **WHEN** combined verification runs in a newly created worktree
- **THEN** verification completes or fails based on repository code and command output
- **AND** it MUST NOT require pre-existing `.repopilot` state files inside the worktree
