## 1. OpenSpec And Harness

- [x] 1.1 Fill V20 `stage_planning.md`, `proposal.md`, `design.md`, `tasks.md`, and spec deltas.
- [x] 1.2 Add long-term `worktree-isolation` spec draft.
- [x] 1.3 Update `.harness/allowed_files.md` for V20 runtime, docs, tests, and worktree boundaries.
- [x] 1.4 Update `.harness/review_checklist.md` with V20 worktree, state-machine, and rollback gates.
- [x] 1.5 Run `openspec validate v20-worktree-isolation --strict`.

## 2. Tests

- [x] 2.1 Add RED tests for repo-local worktree store, create preconditions, detached/locked Git worktree creation, and no-create status query.
- [x] 2.2 Add RED tests for standalone patch apply using isolated `execution_repo_path` and leaving main working tree unchanged.
- [x] 2.3 Add RED tests for combined Patch + Verify using one isolated `execution_repo_path`, including apply-fail and verify-fail branches.
- [x] 2.4 Add RED tests for patch state transitions: `pending -> applied_in_worktree`, `pending -> failed`, and create failure staying `pending`.
- [x] 2.5 Add RED tests for path redaction and cross-user / cross-repo query isolation.

## 3. Implementation

- [x] 3.1 Implement `app/worktrees/store.py` and `app/worktrees/manager.py` for repo-local lifecycle state and read-only lookup.
- [x] 3.2 Add `worktree_create` to `ToolExecutor`, `ToolRegistry`, `PermissionPolicy`, and `ApprovalGate`.
- [x] 3.3 Extend `ToolInvocationContext` and Kernel orchestration for internal worktree creation and `execution_repo_path` propagation.
- [x] 3.4 Update patch lifecycle handling for `applied_in_worktree` and terminal failure semantics.
- [x] 3.5 Integrate worktree lifecycle summaries into persistent audit and `/chat.answer` status queries.

## 4. Docs And Verification

- [x] 4.1 Update README, ARCHITECTURE, PROGRESS, FEATURE_LIST, and HANDOFF for V20.
- [x] 4.2 Run targeted pytest for V20 worktree isolation.
- [x] 4.3 Run `openspec validate --all`.
- [x] 4.4 Run `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`.
- [x] 4.5 Run `git diff --check`.
- [x] 4.6 Run Stage Debt Sweep and record evidence in durable docs and review checklist.
