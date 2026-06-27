## ADDED Requirements

### Requirement: Re-verification Rejects Promoted Worktrees

系统 SHALL treat `promoted` worktrees as ineligible for retained worktree re-verification.

#### Scenario: Promoted worktree cannot be re-verified

- **WHEN** a user requests re-verification for a scoped `promoted` worktree
- **THEN** preflight rejects the request
- **AND** verification MUST NOT run
