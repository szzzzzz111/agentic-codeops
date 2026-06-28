## 1. Planning And Harness

- [x] 1.1 Confirm branch, worktree, recent commits, remote sync, and active OpenSpec state.
- [x] 1.2 Read `AGENTS.md`, required project docs, OpenSpec README, Harness rules, and relevant workflow/review skills.
- [x] 1.3 Inspect the known debt in `docs/PROGRESS.md` and choose the first bounded stage: worktree inspection streaming timeouts.
- [x] 1.4 Create proposal, design, tasks, and `worktree-inspection` spec delta.
- [x] 1.5 Synchronize `.harness/allowed_files.md` and `.harness/review_checklist.md`.
- [x] 1.6 Run internal plan review and classify findings as `fix`, `clarify`, `reject`, or `defer`.
- [x] 1.7 Run Codex independent plan review and classify findings as `fix`, `clarify`, `reject`, or `defer`.
- [x] 1.8 Run `opencode session list` and OpenCode independent plan review using session reuse rules; classify findings as `fix`, `clarify`, `reject`, or `defer`.
- [x] 1.9 Run `openspec validate harden-worktree-inspection-timeouts --strict`.
- [x] 1.10 Stop at implementation confirmation gate.

## 2. Implementation After Confirmation

- [x] 2.1 Add RED tests for hunk count streaming timeout: timeout during read or finalization returns safe partial and kills/reaps the process.
- [x] 2.2 Add RED tests for preview streaming timeout: affected file is omitted, partial is true, and raw exception/path/diff text is not exposed.
- [x] 2.3 Preserve or adapt Git start-failure coverage and add non-zero exit / subprocess-failure coverage if the helper refactor changes that behavior surface.
- [x] 2.4 Implement timeout-bounded streaming Git process handling in `inspection.py`, covering both stdout consumption and process finalization.
- [x] 2.5 Use a Windows-safe mechanism such as watchdog timer/thread kill + reap; do not rely on wait-only timeout or unbounded `communicate()`.
- [x] 2.6 Preserve existing preview limits, redaction, unsafe path omission, count-only untracked semantics, and metadata runner behavior.
- [x] 2.7 Update durable debt documentation only for facts that changed.

## 3. Review, Debt Sweep, Verification, Archive

- [x] 3.1 Run focused `pytest tests/test_worktree_inspection.py -q`.
- [x] 3.2 Run adjacent worktree/AgentLoop/API regressions selected from changed call paths.
- [x] 3.3 Run `openspec validate --all`.
- [x] 3.4 Run `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`.
- [x] 3.5 Run `git diff --check`.
- [x] 3.6 Run final implementation review after the last runtime/test change.
- [x] 3.7 Perform focused Stage Debt Sweep over changed runtime/tests/docs/specs/Harness and directly dependent paths.
- [x] 3.8 Archive the OpenSpec change only after blocking findings are closed and validation passes.
