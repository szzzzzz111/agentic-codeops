## 1. Planning And Harness

- [x] 1.1 Create V23 stage planning, proposal, design, tasks, and spec deltas.
- [x] 1.2 Synchronize `.harness/allowed_files.md` and `.harness/review_checklist.md` before runtime/test edits.
- [x] 1.3 Record V23 as active planning with `passes: false` in durable docs and feature list.
- [x] 1.4 Run internal plan review and strict OpenSpec validation.
- [x] 1.5 Obtain explicit implementation confirmation before modifying runtime code or tests.

## 2. TDD: Commands, Routing, Scope, And Stores

- [x] 2.1 Add RED tests for the four exact confirmed command forms, missing confirmation, extra text/arguments, unsafe syntax, and discussion false positives such as `how to discard changes`.
- [x] 2.2 Add RED tests proving V23 disposal/reconciliation routes after inventory/inspection and before V22 re-verification, patch, standalone verification, audit recovery, and repo-search fallback.
- [x] 2.3 Add RED tests proving unknown, cross-user, and cross-repo ids stop before Git/filesystem/store mutation.
- [x] 2.4 Add RED tests for true no-create patch-store lookup and `mark_status_scoped` qualification while preserving legacy `mark_status`.

## 3. TDD: Blocking Git Metadata Hardening And Preflight

- [x] 3.1 Add RED tests for the shared fixed-argv Git metadata runner timeout, pre-read hard byte limit, non-zero exit, malformed output, no retry, and redacted failure behavior.
- [x] 3.2 Add RED V21/V22 regressions proving inventory/inspection/re-verification use the shared hardened metadata runner without contract changes.
- [x] 3.3 Add RED tests for eligible/ineligible lifecycle, scoped patch existence/status, directory/registry presence matrix, exact path match, registry lock flag, exact linked-worktree `.git`/common-dir/admin-back-reference ownership, and HEAD/base equality.
- [x] 3.4 Add RED tests rejecting path mismatch, HEAD mismatch, damaged metadata, main workspace, managed root, outside paths, symlink/reparse point, and unknown directory ownership.

## 4. TDD: Disposal, Reconciliation, Lifecycle, And Audit

- [x] 4.1 Add RED tests proving normal disposal order is preflight, optional unlock, exact remove, absence post-check, worktree `discarded`, then scoped patch `discarded`.
- [x] 4.2 Add RED tests for every lifecycle transition-table row, including mutation-before failure, `disposal_failed`, cleanup-confirmed/store-failed, patch-only reconciliation, and unsupported-state rejection.
- [x] 4.3 Add RED tests proving repeat disposal/reconciliation after complete closeout is idempotent and performs zero destructive operations.
- [x] 4.4 Add RED tests for each allowed reconciliation residual state and permanent rejection of unsafe/inconsistent states.
- [x] 4.5 Add RED tests proving each step failure stops immediately without retry, rollback, later-step execution, main-workspace mutation, or `git worktree prune`.
- [x] 4.6 Add RED tests proving every recognized attempt writes one scoped redacted `worktree_disposal` audit event and preserves the `/chat` contract.
- [x] 4.7 Add RED tests proving answer, trace, tool calls, and audit do not leak paths, raw Git output, DB paths, environment variables, secrets, diff, patch body, or unknown directory names.
- [x] 4.8 Add RED tests proving disposal/reconciliation never calls repo RAG, patch apply/reapply, verification, promotion, commit, merge, push, or other excluded tools.

## 5. Implementation

- [x] 5.1 Implement strict confirmed disposal/reconciliation parsing, false-positive protection, and V23-before-V22 routing.
- [x] 5.2 Implement the shared bounded timeout-aware Git metadata runner and migrate V21/V22 metadata reads.
- [x] 5.3 Implement true no-create patch-store lookup and scoped patch status update without removing legacy `mark_status`.
- [x] 5.4 Implement scoped fail-closed disposal/reconciliation preflight with exact path, lock, ownership, HEAD/base, and lifecycle classification.
- [x] 5.5 Register and implement approval-gated `worktree_dispose` with strict step ordering, immediate stop, no retry, no prune, and idempotency.
- [x] 5.6 Implement worktree/patch terminal-state updates, safe partial-failure expression, redacted answer/trace/tool-call formatting, and per-attempt persistent audit.

## 6. Docs, Review, And Verification

- [x] 6.1 Update README, ARCHITECTURE, PROGRESS, FEATURE_LIST, HANDOFF, harness, and long-term specs for implemented V23 behavior.
- [x] 6.2 Run V23 targeted tests and focused V20-V22/patch-store/AgentLoop/API/audit regressions.
- [x] 6.3 Run `openspec validate --all`.
- [x] 6.4 Run `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`.
- [x] 6.5 Run `git diff --check`.
- [x] 6.6 Run internal final review and Stage Debt Sweep.
- [x] 6.7 Stop for expected external review and stage-level confirmation before commit/archive/merge/push.



