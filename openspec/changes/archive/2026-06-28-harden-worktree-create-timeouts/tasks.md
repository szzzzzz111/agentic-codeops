## 1. Planning And Harness

- [x] 1.1 Confirm branch, worktree, recent commits, remote sync, and active OpenSpec state.
- [x] 1.2 Read `AGENTS.md`, required project docs, OpenSpec README, Harness rules, and relevant workflow/review skills.
- [x] 1.3 Inspect the known debt in `docs/PROGRESS.md` and choose the bounded stage: worktree create / rollback subprocess timeout hardening.
- [x] 1.4 Create proposal, design, tasks, and `worktree-isolation` spec delta.
- [x] 1.5 Synchronize `.harness/allowed_files.md` and `.harness/review_checklist.md`.
- [x] 1.6 Run internal plan review and classify findings as `fix`, `clarify`, `reject`, or `defer`.
- [x] 1.7 Run Codex independent plan review and classify findings as `fix`, `clarify`, `reject`, or `defer`.
- [x] 1.8 Run `opencode session list` and OpenCode independent plan review using session reuse rules; classify findings as `fix`, `clarify`, `reject`, or `defer`.
- [x] 1.9 Run `openspec validate harden-worktree-create-timeouts --strict`.
- [x] 1.10 Stop at implementation confirmation gate.

## 2. Implementation After Approval

- [x] 2.1 Add RED tests for Git subprocess timeout in worktree create/preflight returning safe failure without raw output.
- [x] 2.2 Add RED tests for bounded stdout/stderr oversize killing/reaping the process and returning safe failure by monkeypatching `WORKTREE_GIT_OUTPUT_MAX_BYTES` small.
- [x] 2.3 Add RED tests preserving `check-ignore` semantics: return code 1 maps to `repopilot_not_ignored`, while return code >1 / timeout / oversize maps to safe `create_failed`.
- [x] 2.4 Add RED tests for rollback unlock/remove timeout or subprocess failure staying best-effort, not hanging create failure, and never returning `created=True`.
- [x] 2.5 Implement bounded manager-local Git subprocess helper with fixed argv, `shell=False`, `GIT_OPTIONAL_LOCKS=0`, `WORKTREE_GIT_TIMEOUT_SECONDS = 10.0`, `WORKTREE_GIT_OUTPUT_MAX_BYTES = 256_000`, and Windows-safe capped reader threads for stdout/stderr.
- [x] 2.6 Route manager preflight, `worktree add`, `check-ignore`, workspace status, and rollback Git calls through the bounded helper.
- [x] 2.7 Preserve existing public reasons, lifecycle states, patch behavior, worktree path layout, and no local absolute path exposure.
- [x] 2.8 Update durable debt documentation only for facts that changed.

## 3. Review, Debt Sweep, Verification, Archive

- [x] 3.1 Run focused `pytest tests/test_worktree_isolation.py -q`.
- [x] 3.2 Run adjacent worktree/AgentLoop/API regressions selected from changed call paths.
- [x] 3.3 Run `openspec validate --all`.
- [x] 3.4 Run `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`.
- [x] 3.5 Run `git diff --check`.
- [x] 3.6 Run final implementation review after the last runtime/test change.
- [x] 3.7 Perform focused Stage Debt Sweep over changed runtime/tests/docs/specs/Harness and directly dependent paths.
- [x] 3.8 Archive the OpenSpec change only after blocking findings are closed and validation passes.
