# Stage Planning

## Stage

- Stage: `V22 Worktree Re-verification`
- Proposed branch: `feature/v22-worktree-re-verification`
- Capability owner:
  - New capability: `worktree-reverification`
  - Modified capabilities: `worktree-isolation`, `verification-runner`, `agent-loop-tool-execution`, `persistent-audit-recovery`, `chat-api`, `harness-development-workflow`
- Previous completed stage: `V21 Worktree Inventory / Inspection`

## Intent

- Problem:
  - V20/V21 retain and safely inspect isolated worktrees, but users cannot explicitly rerun a whitelisted verification command inside an existing retained worktree.
- Why now:
  - Re-verification is the smallest controlled write-capable lifecycle step after inspection and before later disposal/reconciliation or promotion.
- User-visible outcome:
  - `/chat.answer` accepts an explicit scoped worktree re-verification command and returns a bounded redacted result.

## Scope

- In scope:
  - Strictly parsed `worktree verify <worktree_id> <command_label>` and `重新验证 worktree <worktree_id> <command_label>`.
  - Fail-closed scope/directory/Git registry/path/HEAD consistency preflight.
  - Existing `pytest`, `ruff`, and `verify` labels executed only inside the retained worktree.
  - Existing lifecycle updates and one redacted persistent audit record per re-verification request.
- Out of scope:
  - Cleanup, discard, unlock/remove, reconciliation, promotion, patch modification/reapply, main-workspace writes, commit, merge, push, arbitrary shell, background tasks, subagents, connectors, and frontend.
- API contract:
  - Unchanged: `trace_id`, `answer`, `related_files`, `tool_calls`.
- Runtime dependency changes:
  - None; reuse existing Git subprocess, SQLite, Verification Runner, and Harness boundaries.

## Boundaries

- Harness boundaries preserved:
  - Re-verification uses `ToolRegistry -> PermissionPolicy -> ApprovalGate -> ToolExecutor.verification_run`.
  - Preflight produces trusted internal execution context; user input never provides paths, argv, environment, or command parameters.
- Security and audit:
  - Any preflight mismatch fails closed without verification, repair, cleanup, reconciliation, or retry.
  - Full stdout/stderr, absolute paths, DB paths, environment variables, and secrets never enter answer, trace, tool calls, or audit.
  - Preflight failure preserves the previous worktree lifecycle because verification did not execute.
- Retrieval stance:
  - No repo RAG is used for worktree re-verification.

## Tests

- Unit tests:
  - `tests/test_worktree_reverification.py` covers parsing, scope, preflight, execution path, lifecycle, patch immutability, audit, redaction, and failure behavior.
- API / contract tests:
  - AgentLoop and `/chat` tests cover routing priority, stable top-level fields, safe tool calls, and excluded tools.
- Docs / route-map tests:
  - OpenSpec validation and stage docs checks cover V22 planning and implementation state.

## Docs And Harness

- Allowed files to update:
  - V22 OpenSpec artifacts, targeted worktree/kernel/audit/verification/tool runtime, targeted tests, harness, durable docs, and validation scripts.
- Review checklist additions:
  - Strict syntax, fail-closed preflight, worktree-only cwd, lifecycle/patch invariants, per-attempt audit, redaction, no retry/repair, and non-goals.
- Durable docs to update:
  - `README.md`
  - `docs/ARCHITECTURE.md`
  - `docs/PROGRESS.md`
  - `docs/FEATURE_LIST.json`
  - `HANDOFF_TO_NEXT_CHAT.md`

## Human Decisions

- Decision needed:
  - Confirm implementation after planning artifacts, internal plan review, and OpenSpec validation.
- Default recommendation:
  - Implement the locked V22 scope; preserve lifecycle on preflight failure and express rerun history through scoped audit records without schema migration.
