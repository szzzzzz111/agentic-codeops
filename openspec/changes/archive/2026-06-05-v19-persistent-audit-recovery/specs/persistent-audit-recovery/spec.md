## MODIFIED Requirements

### Requirement: Persistent Audit Store

系统 SHALL provide a repo-local persistent audit store for redacted audit summaries at `.repopilot/audit.sqlite3`. Audit records MUST be scoped by `user_id` and repo key. Repo key generation MUST reuse the existing normalized repo identity rule used by repo-local memory.

Audit records SHALL include event id, event type, user id, repo key, optional session id, optional trace id, optional related id, status, summary, structured redacted payload JSON, and creation timestamp.

#### Scenario: Audit records are scoped by user and repo

- **WHEN** two users or two repos create audit events
- **THEN** recovery queries for one `user_id + repo_key` MUST NOT return the other scope's records

#### Scenario: Missing audit store read does not create state

- **WHEN** a user asks for recovery/status and `.repopilot/audit.sqlite3` does not exist
- **THEN** the system returns an empty/no-history answer
- **AND** the system MUST NOT create `.repopilot` or `audit.sqlite3`

### Requirement: Redacted Event Persistence

系统 SHALL persist lightweight trace envelopes for all `/chat` requests and detailed redacted summaries for patch attempts, verification results, and long task events.

Persistent audit payloads MUST NOT include full diffs, full stdout, full stderr, full Evidence Pack content, provider prompts, provider outputs, secrets, DB paths, environment variables, or local absolute paths.

#### Scenario: Patch attempt persistence omits full diff

- **WHEN** a patch proposal, apply attempt, or combined apply/verify flow creates an audit event
- **THEN** the persisted payload MAY include patch id, operation, status, target files, diff hash, changed-file counts, and error class
- **AND** it MUST NOT include the full unified diff text

#### Scenario: Verification persistence omits full command output

- **WHEN** a verification run creates an audit event
- **THEN** the persisted payload MAY include command label, status, exit code, duration, timeout flag, truncation flag, and short redacted excerpts
- **AND** it MUST NOT include full stdout or full stderr

#### Scenario: Long task persistence omits provider raw output

- **WHEN** a long task command or resume creates an audit event
- **THEN** the persisted payload MAY include task id, action, status, current step, and observation summary
- **AND** it MUST NOT include full provider prompt/output or full Evidence Pack content

### Requirement: Read-Only Recovery Answers

系统 SHALL provide read-only recovery/status answers through existing `/chat.answer`. The `/chat` top-level response schema MUST remain unchanged.

Recovery/status queries MUST NOT rerun verification, reapply patches, reopen or resume tasks, modify repository files, commit, push, create worktrees, or trigger repo RAG.

#### Scenario: Recent audit query is read-only

- **WHEN** the user asks for recent audit records or recovery status
- **THEN** the system returns a concise answer with recent redacted events
- **AND** `related_files` remains empty
- **AND** no repo RAG tool call is made
- **AND** no runtime mutation is performed

#### Scenario: Trace lookup is scoped and redacted

- **WHEN** the user asks to view a specific trace id
- **THEN** the system returns only matching records in the current `user_id + repo_key` scope
- **AND** the public answer contains only redacted summaries

### Requirement: Audit Failure Is Non-Blocking

系统 SHALL treat audit persistence as best-effort. Audit write failures MUST NOT fail the primary `/chat` request.

#### Scenario: Audit write failure does not break chat

- **WHEN** the audit store raises an error while recording an event
- **THEN** the primary chat request still returns the same user-facing answer, related files, and safe tool calls it would otherwise return
- **AND** the system MAY record an internal failure summary

### Requirement: V19 Retention Policy

系统 SHALL NOT automatically delete audit records in V19. Recovery list queries SHALL default to the latest 20 records unless a smaller fixed query shape is used by the implementation.

#### Scenario: Audit list is limited without deleting history

- **WHEN** more than 20 audit records exist in a scope
- **THEN** the default recent audit answer returns only the latest 20 records
- **AND** older records remain persisted
