## MODIFIED Requirements

### Requirement: Worktree Lifecycle Produces Persistent Audit Summaries

系统 SHALL record redacted persistent audit summaries for worktree creation, worktree create failure, worktree-backed patch apply, and worktree-backed verification.

V21 worktree inventory and inspection are strict no-state-mutation reads and MUST NOT write persistent audit events. They MAY retain safe request-local trace events, but those events MUST NOT contain preview text, raw Git output, absolute paths, secrets, or untracked file names.

#### Scenario: Worktree inspection does not persist audit

- **WHEN** a user lists or inspects worktrees
- **THEN** the system returns a safe read-only answer
- **AND** it MUST NOT create or update persistent audit state
