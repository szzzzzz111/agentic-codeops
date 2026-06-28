## 1. Planning And Harness

- [x] 1.1 Confirm branch, worktree cleanliness, recent commits, remote sync, and active OpenSpec change.
- [x] 1.2 Create OpenSpec proposal, design, tasks, and spec delta for repo mutation locking.
- [x] 1.3 Synchronize `.harness/allowed_files.md` and `.harness/review_checklist.md` before runtime/test edits.
- [x] 1.4 Run `openspec validate harden-repo-mutation-locking --strict`.
- [x] 1.5 Run internal plan review and classify findings as `fix`, `clarify`, `reject`, or `defer`.
- [x] 1.6 Run Codex independent plan review and classify findings as `fix`, `clarify`, `reject`, or `defer`.
- [x] 1.7 Run OpenCode independent plan review using session reuse rules and classify findings as `fix`, `clarify`, `reject`, or `defer`.
- [x] 1.8 Stop for explicit user confirmation before runtime/tests implementation.

## 2. Candidate TDD Scope After Confirmation

- [x] 2.1 Add RED lock store/guard tests for acquire, release, conflict, owner token mismatch, scope isolation, same-process nested acquisition/provenance behavior, and storage failure.
- [x] 2.2 Add RED tests proving mutation flows refuse safely when the repo mutation lock is already held.
- [x] 2.3 Add RED tests proving V25 promotion holds the lock before main workspace dirty/HEAD preflight and through write, rollback, and state finalization.
- [x] 2.4 Add RED tests proving ordinary confirmed patch apply and combined patch+verify cannot write without a successful lock guard.
- [x] 2.5 Add RED tests for V20 worktree creation/apply, V17/V22 verification_run, and V23 disposal/reconciliation conflict behavior.
- [x] 2.6 Add RED tests proving read-only inventory, inspection, audit recovery, capability status, memory/task status, and repo search do not acquire the mutation lock.
- [x] 2.7 Add RED tests proving lock handling for verification_run does not introduce queueing, retry, background execution, arbitrary shell, or new public response fields.
- [x] 2.8 Add RED fault-injection tests for stale lock encounter, preflight exception, patch write failure, rollback/finalize failure, audit failure, and lock release failure.
- [x] 2.9 Add RED public contract/redaction tests proving lock answers and audit events do not expose absolute paths, DB paths, lock files, raw Git output, patch body, file content, raw exceptions, or secrets.

## 3. Candidate Implementation After Confirmation

- [x] 3.1 Implement a small cross-process repo mutation lock guard/store with deterministic Windows-safe tests.
- [x] 3.2 Wire lock acquisition before mutable preflight/execution for patch apply, worktree create/apply, verification_run, disposal/reconciliation, and verified promotion.
- [x] 3.3 Hold the lock through finalize/rollback and release in all safe completion/failure paths.
- [x] 3.4 Return safe conflict/unavailable responses through existing `/chat.answer` without new public fields.
- [x] 3.5 Add redacted audit summaries for lock attempt, acquired/conflict/unavailable, and release/failure where safe.
- [x] 3.6 Keep read-only flows outside the lock and preserve existing route order.

## 4. Candidate Docs, Review, And Verification After Confirmation

- [x] 4.1 Update only durable docs whose owned facts changed; when archiving, synchronize the centralized `repo-mutation-locking` long-term spec and add references to impacted existing capability specs only if implementation changes their durable contracts.
- [x] 4.2 Run focused lock tests and adjacent patch/worktree/promotion/audit/AgentLoop/API regressions.
- [x] 4.3 Run `openspec validate --all`.
- [x] 4.4 Run `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`.
- [x] 4.5 Run `git diff --check`.
- [x] 4.6 Run final implementation review and Stage Debt Sweep after the last runtime/test change.
