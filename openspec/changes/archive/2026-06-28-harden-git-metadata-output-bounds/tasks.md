## 1. Planning And Harness

- [x] 1.1 Confirm branch, worktree, recent commits, remote sync, and active OpenSpec state.
- [x] 1.2 Read `AGENTS.md`, required project docs, OpenSpec README, Harness rules, and relevant workflow/review skills.
- [x] 1.3 Inspect the residual subprocess debt and choose the bounded stage: shared Git metadata output bounds.
- [x] 1.4 Create proposal, design, tasks, and spec deltas.
- [x] 1.5 Synchronize `.harness/allowed_files.md` and `.harness/review_checklist.md`.
- [x] 1.6 Run internal plan review and classify findings as `fix`, `clarify`, `reject`, or `defer`.
- [x] 1.7 Run Codex independent plan review and classify findings as `fix`, `clarify`, `reject`, or `defer`.
- [x] 1.8 Run `opencode session list` and OpenCode independent plan review using session reuse rules; classify findings as `fix`, `clarify`, `reject`, or `defer`.
- [x] 1.9 Run `openspec validate harden-git-metadata-output-bounds --strict`.
- [x] 1.10 Stop at implementation confirmation gate.

## 2. Implementation After Approval

- [x] 2.1 Add RED tests for metadata timeout killing and bounded reaping.
- [x] 2.2 Add RED tests for stdout oversize killing/reaping before normal process exit and returning `None` without retaining oversize bytes.
- [x] 2.3 Add RED tests for stdout read failure or reader non-completion returning `None`.
- [x] 2.4 Add regression coverage for non-zero exit returning `None`.
- [x] 2.5 Add cap-edge regression: exactly `max_bytes` may return bytes, while `max_bytes + 1` returns `None`.
- [x] 2.6 Add regression coverage that disposal postcheck metadata unavailability after mutation remains safe failure, not success.
- [x] 2.7 Implement bounded stdout pipe reader in `app/worktrees/git_metadata.py` with `GIT_METADATA_REAP_TIMEOUT_SECONDS = 1.0` and `GIT_METADATA_READER_JOIN_TIMEOUT_SECONDS = 1.0`.
- [x] 2.8 Preserve fixed argv, `shell=False`, `GIT_OPTIONAL_LOCKS=0`, stderr discard, bounded post-kill reap, no retry, no repair, and no raw output exposure.
- [x] 2.9 Preserve existing `git_metadata_text()` and `registry_entries()` caller semantics.
- [x] 2.10 Update durable documentation only for facts that changed.

## 3. Review, Debt Sweep, Verification, Archive

- [x] 3.1 Run focused `pytest tests/test_worktree_disposal.py -q`.
- [x] 3.2 Run adjacent worktree inspection/reverification/promotion/disposal regressions.
- [x] 3.3 Run `ruff check .`.
- [x] 3.4 Run `openspec validate --all`.
- [x] 3.5 Run `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`.
- [x] 3.6 Run `git diff --check`.
- [x] 3.7 Run final implementation review after the last runtime/test change.
- [x] 3.8 Perform focused Stage Debt Sweep over changed runtime/tests/docs/specs/Harness and directly dependent paths.
- [x] 3.9 Archive the OpenSpec change only after blocking findings are closed and validation passes.
