# Stage Planning

## Stage

- Stage: `V23 Worktree Disposal / Reconciliation`
- Proposed branch: `feature/v23-worktree-disposal-reconciliation`
- Capability owner:
  - New capability: `worktree-disposal-reconciliation`
  - Modified capabilities: `worktree-isolation`, `worktree-inspection`, `worktree-reverification`, `safe-patch-authoring`, `agent-loop-tool-execution`, `persistent-audit-recovery`, `chat-api`, `harness-development-workflow`
- Previous completed stage: `V22 Worktree Re-verification`

## Intent

- Problem:
  - V20-V22 can create, inspect, and re-verify retained worktrees, but users cannot explicitly dispose them or safely reconcile a partially completed disposal.
- Why now:
  - Disposal closes the retained-worktree lifecycle before V24 verified promotion. V22 also recorded blocking Git metadata timeout and pre-read output-bound debt that must be fixed before destructive decisions are allowed.
- User-visible outcome:
  - `/chat.answer` accepts exact confirmed discard/reconcile commands and returns a bounded redacted result without changing the top-level contract.

## Scope

- In scope:
  - Exact confirmed discard/reconcile commands, scoped fail-closed preflight, controlled unlock/remove/delete/state-update ordering, narrow reconciliation, idempotency, redacted persistent audit, and blocking Git metadata runner hardening.
- Out of scope:
  - Patch promotion/reapply/mutation, commit, merge, push, implicit reconciliation, automatic repair/retry, arbitrary shell, background work, subagents, connectors, frontend, and unknown or cross-scope cleanup.
- API contract:
  - Unchanged: `trace_id`, `answer`, `related_files`, `tool_calls`.
- Runtime dependency changes:
  - None; use stdlib subprocess/tempfile/SQLite and existing Harness boundaries.

## Boundaries

- Harness boundaries preserved:
  - Disposal executes only through `ToolRegistry -> PermissionPolicy -> ApprovalGate -> ToolExecutor.worktree_dispose`.
  - Trusted paths are reconstructed from resolved repo root, fixed managed root, and scoped validated worktree id.
- Security and audit:
  - No `git worktree prune`; no user-controlled argv/path/cwd; no deletion without linked-worktree ownership attestation.
  - Every recognized attempt is persistently auditable with redacted step/terminal-state summaries.
- Retrieval stance:
  - Disposal/reconciliation MUST NOT call repo RAG.

## Tests

- Unit tests:
  - New disposal tests cover parsing, routing, scope, preflight classes, lifecycle transitions, strict order, idempotency, reconciliation, failures, audit, and redaction.
- API / contract tests:
  - AgentLoop and `/chat` tests cover stable fields, safe tool calls, V23-before-V22 routing, and excluded tools.
- Docs / route-map tests:
  - OpenSpec validation and stage docs checks cover active V23 planning and later implementation parity.

## Docs And Harness

- Allowed files to update:
  - V23 OpenSpec artifacts, targeted worktree/kernel/tool/audit/patch-store runtime, targeted tests, harness, durable docs, and validation scripts.
- Review checklist additions:
  - Exact confirmation, false-positive prevention, blocking Git metadata hardening, no-create/scoped stores, ownership proof, lifecycle matrix, strict ordering, partial failures, idempotency, audit/redaction, and non-goals.
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
  - Implement the narrow safe reconciliation set; permanently reject path/HEAD/metadata/scope uncertainty and keep promotion for V24.
