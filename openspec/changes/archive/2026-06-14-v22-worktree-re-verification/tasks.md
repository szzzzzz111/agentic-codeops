## 1. Planning And Harness

- [x] 1.1 Create V22 stage planning, proposal, design, tasks, and spec deltas.
- [x] 1.2 Synchronize `.harness/allowed_files.md` and `.harness/review_checklist.md` before runtime edits.
- [x] 1.3 Record V22 as active planning with `passes: false` in durable docs and feature list.
- [x] 1.4 Run internal plan review and `openspec validate v22-worktree-re-verification --strict`.
- [x] 1.5 Obtain explicit implementation confirmation before modifying runtime code or tests.

## 2. TDD: Command, Scope, And Preflight

- [x] 2.1 Add RED tests for exact English/Chinese command forms and rejection of unknown labels, extra arguments, paths, environment variables, pipes, redirection, shell syntax, and partial matches.
- [x] 2.2 Add RED tests proving unknown, cross-user, and cross-repo worktree ids stop before Git inspection and verification.
- [x] 2.3 Add RED tests for missing directory, missing registry entry, registry-path mismatch, and HEAD/base mismatch fail-closed behavior.
- [x] 2.4 Add RED tests proving malformed Git output and Git exceptions do not repair, reconcile, cleanup, retry, create state, or run verification.

## 3. TDD: Execution, Lifecycle, And Patch Invariants

- [x] 3.1 Add RED tests proving `verification_run` receives only the trusted retained worktree execution path and the main workspace remains unchanged.
- [x] 3.2 Add RED tests proving `pytest`, `ruff`, and `verify` reuse the existing ToolRegistry, PermissionPolicy, ApprovalGate, ToolExecutor, timeout, limits, and redaction behavior.
- [x] 3.3 Add RED tests proving success sets `verification_succeeded` and executed failure/timeout/unavailable/exception sets `verification_failed`.
- [x] 3.4 Add RED tests proving preflight and approval failures preserve the previous lifecycle because verification did not execute.
- [x] 3.5 Add RED tests proving the related patch remains `applied_in_worktree` after success, execution failure, and preflight failure.

## 4. TDD: Audit, Contract, And Non-Goals

- [x] 4.1 Add RED tests proving every recognized re-verification request attempts one scoped redacted `verification_result` audit related to the worktree id.
- [x] 4.2 Add RED tests proving audit distinguishes `attempt_kind=worktree_reverification`, execution attempted/not attempted, preflight outcome, and each rerun without schema migration.
- [x] 4.3 Add RED tests proving full stdout/stderr, absolute paths, `.git`/DB paths, environment variables, secrets, raw Git output, diff, and preview never enter answer, trace, tool calls, or audit.
- [x] 4.4 Add RED tests proving `/chat` top-level contract remains unchanged and preflight failures expose no verification tool call.
- [x] 4.5 Add RED tests proving the flow does not call repo RAG, patch apply/manager/store, cleanup, reconciliation, promotion, or other excluded tools.

## 5. Implementation

- [x] 5.1 Implement strict worktree re-verification parsing and routing priority.
- [x] 5.2 Implement narrow scoped fail-closed preflight using trusted metadata and fixed Git argv without full V21 inspection.
- [x] 5.3 Reuse the existing verification permission/approval/executor path with the trusted worktree execution path.
- [x] 5.4 Update existing worktree lifecycle only after execution and preserve patch state.
- [x] 5.5 Add per-request redacted re-verification audit mapping and safe answer/trace formatting.

## 6. Docs, Review, And Verification

- [x] 6.1 Update README, ARCHITECTURE, PROGRESS, FEATURE_LIST, HANDOFF, harness, and long-term specs for implemented V22 behavior.
- [x] 6.2 Run V22 targeted tests and relevant AgentLoop/API/audit/V20/V21 regressions.
- [x] 6.3 Run `openspec validate --all`.
- [x] 6.4 Run `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`.
- [x] 6.5 Run `git diff --check`.
- [x] 6.6 Run internal final review and Stage Debt Sweep.
- [x] 6.7 Stop for expected external review and stage-level confirmation before commit/archive/merge/push.
