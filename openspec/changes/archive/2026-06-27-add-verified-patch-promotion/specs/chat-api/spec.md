## ADDED Requirements

### Requirement: Verified Patch Promotion Reuses The Existing Chat Contract

系统 SHALL return Verified Patch Promotion results through existing `/chat.answer` and safe `tool_calls` semantics. V25 MUST NOT add required or optional `/chat` top-level fields or a standalone promotion API.

Promotion answers MAY identify safe worktree id, patch id, preflight result, and final promotion state. They MUST NOT expose retained worktree filesystem paths, local absolute paths, `.git` paths, DB paths, raw Git output, full diff, patch body, copied file content, or secrets.

#### Scenario: Promotion answer preserves response schema

- **WHEN** `/chat` returns a promotion result
- **THEN** the response still contains only `trace_id`, `answer`, `related_files`, and `tool_calls`
- **AND** the answer does not expose local paths or raw Git output
