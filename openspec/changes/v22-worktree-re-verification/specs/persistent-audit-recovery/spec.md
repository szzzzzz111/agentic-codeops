## ADDED Requirements

### Requirement: Worktree Re-verification Attempts Are Persistently Auditable

系统 SHALL attempt to persist one redacted `verification_result` event for every recognized retained worktree re-verification request. The event MUST be scoped by current `user_id + repo_key`, related to the worktree id, and distinguish re-verification from standalone or initial combined verification.

The event MUST include `attempt_kind=worktree_reverification` and `related_id=<worktree_id>`. Its payload MAY additionally include the execution-attempted flag, preflight outcome/reason, command label, verification status, exit code, duration, timeout, and truncation flags. It MUST NOT contain full stdout/stderr, absolute paths, `.git` paths, DB paths, environment variables, secrets, raw Git output, diff, or preview.

#### Scenario: Multiple reruns remain distinguishable

- **WHEN** a scoped worktree receives multiple re-verification requests
- **THEN** each request produces a separate related redacted audit event
- **AND** the matching event count expresses the rerun count without a schema migration
