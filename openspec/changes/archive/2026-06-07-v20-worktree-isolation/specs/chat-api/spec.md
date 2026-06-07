## ADDED Requirements

### Requirement: Worktree Results Reuse The Existing Chat Contract

系统 SHALL return worktree-backed patch results and worktree status answers through the existing `/chat` response contract. V20 MUST NOT add new required or optional top-level `/chat` fields.

Public worktree answers MAY include safe `worktree_id`, patch id, status summary, base commit, and verification summary. Public answers MUST NOT expose local absolute paths, `.git` paths, DB paths, or full Git output.

#### Scenario: Worktree-backed patch apply keeps contract

- **WHEN** `/chat` returns a worktree-backed patch result
- **THEN** the response still contains only `trace_id`, `answer`, `related_files`, and `tool_calls`
- **AND** `answer` may mention `worktree_id`
- **AND** `answer` MUST NOT expose the worktree filesystem path
