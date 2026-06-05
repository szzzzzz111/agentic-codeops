## MODIFIED Requirements

### Requirement: Verification Results Produce Persistent Audit Summaries

系统 SHALL record redacted persistent audit summaries for standalone verification runs and patch verify loop verification runs when an audit store is available.

Verification audit summaries MAY include command label, status, exit code, duration, timeout flag, truncation flag, and short redacted excerpts. Verification audit summaries MUST NOT persist or expose full stdout, full stderr, environment variables, DB paths, local absolute paths, API keys, or secrets.

#### Scenario: Verification audit summary is safe

- **WHEN** `verification_run` completes, fails, or times out
- **THEN** the persistent audit event records command label, status, exit code, duration, and truncation/timeout flags
- **AND** it MUST NOT contain full stdout or full stderr
