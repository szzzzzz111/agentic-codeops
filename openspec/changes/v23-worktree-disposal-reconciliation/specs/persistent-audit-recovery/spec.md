## ADDED Requirements

### Requirement: Worktree Disposal Attempts Are Persistently Auditable

系统 SHALL attempt to persist one redacted `worktree_disposal` event for every recognized V23 discard/reconcile attempt. The event MUST be scoped by current `user_id + repo_key` and related to the requested worktree id.

The event MAY include attempt kind, confirmation, preflight classification, completed step, failed step, mutation-attempted flag, and safe worktree/patch terminal state. It MUST NOT contain absolute paths, raw Git output, DB paths, environment variables, secrets, diff, patch body, or unknown directory names.

#### Scenario: Partial failure is recoverable from safe audit

- **WHEN** disposal stops after a destructive step
- **THEN** one safe related audit event identifies the completed and failed steps
- **AND** it does not expose raw local state
