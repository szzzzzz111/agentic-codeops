## ADDED Requirements

### Requirement: Worktree Disposal Reuses The Existing Chat Contract

系统 SHALL return V23 disposal/reconciliation results through the existing `/chat.answer` and safe `tool_calls` semantics. V23 MUST NOT add required or optional top-level fields or a standalone disposal API.

`related_files` MUST remain empty. Rejected/preflight-failed/idempotent results MUST expose no execution tool call. Executed results MAY expose only a safe `worktree_dispose` summary without paths or raw Git output.

#### Scenario: Disposal answer keeps chat schema

- **WHEN** `/chat` returns a V23 disposal/reconciliation result
- **THEN** the response contains only `trace_id`, `answer`, `related_files`, and `tool_calls`
- **AND** it MUST NOT expose local paths or raw Git output
