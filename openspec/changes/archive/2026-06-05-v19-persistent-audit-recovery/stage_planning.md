# Stage Planning

## Stage

- Stage: `V19 Persistent Audit / Recovery`
- Proposed branch: `feature/v19-persistent-audit-recovery`
- Capability owner:
  - New capability: `persistent-audit-recovery`
  - Modified capabilities: `agent-loop-tool-execution`, `chat-api`, `safe-patch-authoring`, `verification-runner`, `long-task-agent-execution`, `harness-development-workflow`
- Previous completed stage: `V18 Patch + Verify Loop` plus post-merge closeout debt remediation on `main` commit `8b93330`

## Intent

- Problem:
  - RepoPilot currently keeps trace, patch, verification, and long task summaries in in-memory or feature-local stores only. A later chat cannot ask what just happened in a durable, scoped, redacted way.
- Why now:
  - V16-V18 created the patch/apply/verify loop. The next lightweight industrial harness slice is persistent audit/recovery before worktree isolation.
- User-visible outcome:
  - Users can ask recovery/status questions through existing `/chat.answer`, such as recent audit records, recent verification results, or a specific trace/patch summary.

## Scope

- In scope:
  - Repo-local SQLite audit store for redacted summaries of all `/chat` trace envelopes and detailed patch/verification/long task events.
  - Read-only recovery/status intent through the existing chat route.
- Out of scope:
  - V20 Worktree Isolation.
  - Real subagents, connectors, notifications, heartbeat/cron, always-on assistant.
  - Replay, rerun, reapply, resume, commit, push, or automatic repair.
- API contract:
  - `/chat` top-level response schema remains unchanged: `trace_id`, `answer`, `related_files`, `tool_calls`.
  - Recovery/status output is formatted into `answer`.
- Runtime dependency changes:
  - No external dependency. Use stdlib SQLite through `sqlite3`.

## Boundaries

- Harness boundaries preserved:
  - Patch and verification still flow through `ToolExecutor`, `PermissionPolicy`, and `ApprovalGate`.
  - Audit is best-effort and MUST NOT change primary request behavior when persistence fails.
- Security and audit:
  - Persistent payloads MUST NOT include full diff, full stdout/stderr, full Evidence Pack, provider prompts/outputs, secrets, DB paths, or local absolute paths.
- Retrieval stance:
  - Recovery/status intent is read-only and MUST NOT call repo RAG after it matches.

## Tests

- Unit tests:
  - `tests/test_persistent_audit.py` covers schema, scoping, ordering, missing-store behavior, redaction, capping, and non-persistence of dangerous payloads.
- API / contract tests:
  - Chat recovery/status keeps existing top-level fields and does not invoke repo RAG.
- Docs / route-map tests:
  - OpenSpec validation, default verify, Stage Debt Sweep, and closeout docs gates.

## Docs And Harness

- Allowed files to update:
  - OpenSpec change artifacts, `app/audit/**`, targeted AgentLoop hooks, targeted tests, docs, and harness files.
- Review checklist additions:
  - audit redaction, read-only recovery, missing-store no-create, failure non-blocking, schema unchanged, recovery no-RAG, complete spec delta coverage, Stage Debt Sweep evidence, post-merge durable docs, branch retention.
- Durable docs to update:
  - `README.md`
  - `docs/ARCHITECTURE.md`
  - `docs/PROGRESS.md`
  - `docs/FEATURE_LIST.json`
  - `HANDOFF_TO_NEXT_CHAT.md`

## Human Decisions

- Decision needed:
  - Audit scope, recovery interface, and retention policy.
- Default recommendation:
  - Locked by user: all `/chat` lightweight trace envelopes; existing `/chat.answer`; unlimited retention with default query limit 20.
