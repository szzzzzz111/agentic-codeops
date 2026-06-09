## MODIFIED Requirements

### Requirement: Worktree Status Queries Are Read-Only

系统 SHALL support read-only scoped inventory and detailed inspection through existing `/chat.answer`. V21 inspection replaces the V20 narrow per-id status behavior while preserving the existing status command phrases.

Missing worktree stores, empty scopes, unknown ids, missing directories, and Git registry inconsistencies MUST NOT create or modify repo-local state. Inspection answers MAY include safe identifiers, lifecycle metadata, verification summary, tracked-change statistics, consistency findings, and bounded safe preview. They MUST NOT expose local absolute paths, `.git` paths, DB paths, raw Git output, raw diff, secrets, or untracked file names.

#### Scenario: Missing worktree store query does not create state

- **WHEN** a user asks for inventory or inspection and `.repopilot/worktrees.sqlite3` does not exist
- **THEN** the system returns an empty or not-found answer
- **AND** it MUST NOT create `.repopilot` or the worktree store
