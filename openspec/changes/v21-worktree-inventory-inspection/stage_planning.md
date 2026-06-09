# Stage Planning

## Stage

- Stage: `V21 Worktree Inventory / Inspection`
- Proposed branch: `feature/v21-worktree-inventory-inspection`
- Capability owner:
  - New capability: `worktree-inspection`
  - Modified capabilities: `worktree-isolation`, `agent-loop-tool-execution`, `chat-api`, `persistent-audit-recovery`, `harness-development-workflow`
- Previous completed stage: `V20 Worktree Isolation`

## Intent

- Problem:
  - V20 retains isolated worktrees but only exposes a narrow status summary; operators cannot safely inventory or inspect retained worktree content and consistency.
- Why now:
  - Read-only visibility is the lowest-risk next slice before re-verification, disposal/reconciliation, or promotion.
- User-visible outcome:
  - `/chat.answer` can list the current scope's worktrees and inspect one worktree with bounded, redacted evidence.

## Scope

- In scope:
  - Scoped inventory and detailed inspection of one retained worktree.
  - Lifecycle, patch/base, tracked changes, diffstat, hunk count, verification summary, consistency checks, and bounded preview.
- Out of scope:
  - Re-verification, cleanup, discard, unlock/remove, reconciliation, promotion, main-workspace writes, commit, merge, push, background tasks, subagents, connectors, and frontend.
- API contract:
  - Unchanged: `trace_id`, `answer`, `related_files`, `tool_calls`.
- Runtime dependency changes:
  - None; use fixed Git argv and stdlib SQLite.

## Boundaries

- Harness boundaries preserved:
  - Inventory / inspection remain read-only and do not enter approval or write-tool paths.
  - `AgentLoop.run()` keeps its unified wrapper; audit skip is decided by safe internal trace event type.
- Security and audit:
  - Preview paths come only from machine-readable Git output.
  - Raw diff exists only in the current request stack and is never persisted.
  - Inventory / inspection skip persistent audit to preserve the no-state-mutation guarantee.
- Retrieval stance:
  - No repo RAG is used for inventory / inspection.

## Tests

- Unit tests:
  - `tests/test_worktree_inspection.py` covers scope, no-create reads, Git consistency, preview safety, limits, and untracked count-only output.
- API / contract tests:
  - AgentLoop and `/chat` tests cover route replacement, stable schema, no write tools, and audit skip.
- Docs / route-map tests:
  - OpenSpec validation and stage docs checks cover the V21 planning/implementation state.

## Docs And Harness

- Allowed files to update:
  - V21 OpenSpec artifacts, targeted worktree/kernel/audit/file-tool runtime, targeted tests, harness, durable docs, and validation scripts.
- Review checklist additions:
  - Git-derived paths, preview budgets, count-only untracked output, audit skip, scope isolation, and no-state-mutation.
- Durable docs to update:
  - `README.md`
  - `docs/ARCHITECTURE.md`
  - `docs/PROGRESS.md`
  - `docs/FEATURE_LIST.json`
  - `HANDOFF_TO_NEXT_CHAT.md`

## Human Decisions

- Decision needed:
  - Confirm implementation after planning artifacts and OpenSpec validation.
- Default recommendation:
  - Implement the locked V21 scope without adding any V22-V24 behavior.
