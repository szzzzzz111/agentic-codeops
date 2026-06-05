## MODIFIED Requirements

### Requirement: Patch Attempts Produce Persistent Audit Summaries

系统 SHALL record redacted persistent audit summaries for patch proposal, apply, failure, expiry, and combined patch/verify attempts when an audit store is available.

Patch audit summaries MAY include patch id, operation, status, target files, diff hash, changed-file counts, and safe error class. Patch audit summaries MUST NOT persist or expose the full unified diff, full Evidence Pack, provider prompt/output, DB path, local absolute path, API key, or secret.

#### Scenario: Patch apply audit summary is safe

- **WHEN** a pending patch is applied or fails to apply
- **THEN** the persistent audit event records safe patch identifiers and status
- **AND** it MUST NOT contain full diff text
