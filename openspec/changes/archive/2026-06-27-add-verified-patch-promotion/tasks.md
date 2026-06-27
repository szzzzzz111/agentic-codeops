## 1. Planning And Harness

- [x] 1.1 Confirm branch, worktree cleanliness, recent commits, remote sync, and active OpenSpec change.
- [x] 1.2 Create V25 OpenSpec proposal, design, tasks, and spec delta for Verified Patch Promotion planning.
- [x] 1.3 Synchronize `.harness/allowed_files.md` and `.harness/review_checklist.md` for V25 planning before runtime/test edits.
- [x] 1.4 Run internal plan review and classify findings as `fix`, `clarify`, `reject`, or `defer`.
- [x] 1.5 Run Codex independent plan review and classify findings as `fix`, `clarify`, `reject`, or `defer`.
- [x] 1.6 Run OpenCode independent plan review using session reuse rules and classify findings as `fix`, `clarify`, `reject`, or `defer`.
- [x] 1.7 Run `openspec validate add-verified-patch-promotion --strict`.
- [x] 1.8 Stop for explicit user confirmation before runtime/tests implementation.

## 2. Candidate TDD Scope After Confirmation

- [x] 2.1 Add RED parser/routing tests for exact confirmed promotion commands, missing confirmation, extra text, unsafe ids, shell syntax, and false positives.
- [x] 2.2 Add RED routing tests proving promotion is handled after disposal/reconciliation and before re-verification, patch handling, standalone verification, audit recovery, capability status, and repo-search fallback.
- [x] 2.3 Add RED scope tests proving unknown, cross-user, and cross-repo worktree ids stop before Git/filesystem/patch mutation.
- [x] 2.4 Add RED preflight tests for `verification_succeeded`, `applied_in_worktree`, clean main workspace, `HEAD == base_commit`, expected path, Git registry, metadata, and retained worktree HEAD consistency.
- [x] 2.5 Add RED content-integrity tests proving promotion compares retained worktree content to the stored controlled patch expectation and rejects tampered worktree files.
- [x] 2.6 Add RED tests proving promotion writes the main workspace only through existing `patch_apply` / Harness approval and never copies files from the worktree.
- [x] 2.7 Add RED permission-context tests proving ordinary `applied_in_worktree` patch apply is rejected while a fully preflighted promotion context is approved.
- [x] 2.8 Add RED tests proving promotion failure cannot leave the main workspace partially promoted, including write failure and restore/rollback failure semantics if applicable.
- [x] 2.9 Add RED failure tests for dirty main workspace, base drift, stale patch hash, missing patch DB, missing worktree DB, malformed Git metadata, approval denial, patch apply failure, state update failure, and audit failure.
- [x] 2.10 Add RED state-machine tests for successful `promoted` patch/worktree states, repeated promotion safe rejection, promoted worktree rejection by re-verification/disposal/re-promotion, preflight failure, execution failure, and post-apply state update failure semantics chosen by plan review.
- [x] 2.11 Add RED audit and public contract tests proving no new `/chat` fields and no leakage of absolute paths, raw Git output, DB paths, full diff, patch body, secrets, or worktree file content.

## 3. Candidate Implementation After Confirmation

- [x] 3.1 Implement strict promotion parsing and routing at the chosen AgentLoop position.
- [x] 3.2 Implement scoped fail-closed promotion preflight.
- [x] 3.3 Implement stored-patch expected-content integrity validation without trusting worktree files.
- [x] 3.4 Prove or implement promotion-safe atomic/staged main-workspace writes before enabling promotion.
- [x] 3.5 Implement distinct promotion-safe permission context without broadening ordinary patch apply approval.
- [x] 3.6 Reuse `patch_apply` through `ToolExecutor`, `PermissionPolicy`, and `ApprovalGate` for main workspace writes.
- [x] 3.7 Implement `promoted` patch/worktree state transitions and redacted answer formatting.

## 4. Candidate Docs, Review, And Verification After Confirmation

- [x] 4.1 Update only durable docs whose owned facts changed; do not claim promotion is implemented before runtime is complete.
- [x] 4.2 Run focused promotion tests and adjacent patch/worktree/audit/AgentLoop/API regressions.
- [x] 4.3 Run `openspec validate --all`.
- [x] 4.4 Run `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`.
- [x] 4.5 Run `git diff --check`.
- [x] 4.6 Run final implementation review and Stage Debt Sweep after the last runtime/test change.
