## ADDED Requirements

### Requirement: Promotion Attempts Are Persistently Auditable

系统 SHALL attempt to persist one redacted `patch_promotion` event for every recognized Verified Patch Promotion request. The event MUST be scoped by current `user_id + repo_key` and related to the requested worktree id and patch id when safely known.

The event MAY include confirmation, preflight classification, execution-attempted flag, safe state transition, and safe error class. It MUST NOT contain local absolute paths, `.git` paths, DB paths, raw Git output, full diff, patch body, copied file content, environment variables, secrets, raw exception text, or unknown directory names.

#### Scenario: Promotion preflight failure is auditable

- **WHEN** a recognized promotion request fails preflight
- **THEN** one safe related audit event records that execution was not attempted
- **AND** no main workspace mutation occurs
