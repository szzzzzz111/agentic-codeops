## ADDED Requirements

### Requirement: Worktree Re-verification Reuses The Existing Chat Contract

系统 SHALL return V22 re-verification results through the existing `/chat.answer` and safe `tool_calls` semantics. V22 MUST NOT add required or optional top-level `/chat` fields or a standalone verification/worktree API.

`related_files` MUST remain empty. Preflight failures MUST expose no verification tool call. Successful preflight MAY expose only the existing safe `verification_run` tool-call summary.

#### Scenario: Re-verification answer keeps chat schema

- **WHEN** `/chat` returns a V22 re-verification result
- **THEN** the response contains only `trace_id`, `answer`, `related_files`, and `tool_calls`
- **AND** it MUST NOT expose the trusted worktree execution path
