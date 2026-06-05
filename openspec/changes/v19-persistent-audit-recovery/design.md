## Current Behavior

- `trace_id` is generated per request, but trace events are in-memory execution records.
- Patch attempts are tracked in `.repopilot/patches.sqlite3`, but that store is not a general audit/recovery log and may contain patch-specific lifecycle data.
- Verification results are returned as redacted summaries but are not persisted across sessions.
- Long task state is persisted in `.repopilot/tasks.sqlite3`, but cross-feature recovery cannot ask for a unified audit timeline.

## Target Behavior

- `app/audit/` provides a repo-local SQLite audit store at `.repopilot/audit.sqlite3`.
- Audit rows are scoped by `user_id + repo_key`, with optional `session_id`, `trace_id`, and `related_id`.
- All `/chat` requests write a lightweight trace envelope: route/status/tool names/counts and safe identifiers only.
- Patch, verification, and long task flows write more specific redacted event payloads.
- Recovery/status intent reads the audit store without mutating runtime state and formats concise answers through existing `/chat.answer`.
- If the audit DB does not exist, recovery/status reads return an empty result without creating `.repopilot`.
- Audit write failures are swallowed into internal trace/failure summaries and do not change primary `/chat` behavior.

## Data Model

Use one table:

- `event_id TEXT PRIMARY KEY`
- `event_type TEXT NOT NULL`
- `user_id TEXT NOT NULL`
- `repo_key TEXT NOT NULL`
- `session_id TEXT`
- `trace_id TEXT`
- `related_id TEXT`
- `status TEXT NOT NULL`
- `summary TEXT NOT NULL`
- `payload_json TEXT NOT NULL`
- `created_at TEXT NOT NULL`

Indexes:

- `(user_id, repo_key, created_at)`
- `(user_id, repo_key, trace_id)`
- `(user_id, repo_key, related_id)`

Retention:

- V19 does not delete audit rows automatically.
- List queries default to the latest 20 records.

## Event Payloads

- `trace`: route, status, tool names, tool result count, safe branch of AgentLoop, no full answer text.
- `patch_attempt`: patch id, operation, status, target files, diff hash, changed-file counts, error class; no full diff.
- `verification_result`: command label, status, exit code, duration, timeout/truncated flags, short redacted excerpts only.
- `task_event`: task id, command/action, status, current step index/title, observation summary; no provider raw output.

All payload text must be capped and redacted before persistence.

## Recovery Routing

AgentLoop route priority is fixed:

1. memory command
2. long task command
3. assistant control surface
4. patch command / patch intent
5. verification intent
6. audit recovery/status intent
7. capability/status intent
8. repo_search / chat_only fallback

Recovery is after patch/verification to avoid swallowing execution confirmations. It is before repo search so status/recovery questions never call repo RAG.

## Security And Failure Boundaries

- Do not persist full diffs, full stdout/stderr, full Evidence Pack, provider prompt/output, secrets, DB paths, environment variables, or local absolute paths.
- Do not expose internal trace or DB path in public `/chat` fields.
- Do not create audit DB for read-only recovery queries when it is absent.
- Do not rerun verification, reapply patch, reopen/resume task, commit, push, or create worktree from recovery/status intent.

## Process Boundary

Stage Debt Sweep, skill edits, and handoff discipline are project workflow. If `.codex/skills/**` is edited during V19, the edit is a local process-doc change only and MUST NOT be described as RepoPilot runtime behavior.
