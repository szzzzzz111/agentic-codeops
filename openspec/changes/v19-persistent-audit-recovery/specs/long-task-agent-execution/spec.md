## MODIFIED Requirements

### Requirement: Long Task Events Produce Persistent Audit Summaries

系统 SHALL record redacted persistent audit summaries for long task create, status, pause, resume, supplement, reopen, archive, and step-result events when an audit store is available.

Long task audit summaries MAY include task id, command/action, status, current step index/title, and observation summary. Long task audit summaries MUST NOT persist or expose full scratch, full ReAct trace, full Evidence Pack, provider prompt/output, DB path, local absolute path, API key, or secret.

#### Scenario: Long task resume audit summary is safe

- **WHEN** a long task resume/run command advances or attempts to advance one step
- **THEN** the persistent audit event records task id, action, status, and a redacted step summary
- **AND** it MUST NOT contain full provider output or full Evidence Pack content
