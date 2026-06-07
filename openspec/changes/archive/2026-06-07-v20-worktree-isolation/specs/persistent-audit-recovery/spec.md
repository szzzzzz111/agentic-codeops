## ADDED Requirements

### Requirement: Worktree Lifecycle Produces Persistent Audit Summaries

系统 SHALL record redacted persistent audit summaries for worktree creation, worktree create failure, worktree-backed patch apply, worktree-backed verification, and worktree status lookup.

Worktree audit summaries MAY include `worktree_id`, patch id, base commit, lifecycle status, verification label/status, and changed-file counts. They MUST NOT include local absolute paths, `.git` paths, DB paths, full Git stdout/stderr, full diff text, or secrets.

#### Scenario: Worktree audit summary is safe

- **WHEN** a worktree is created or queried
- **THEN** the persistent audit event records safe identifiers and status
- **AND** it MUST NOT contain the worktree filesystem path
