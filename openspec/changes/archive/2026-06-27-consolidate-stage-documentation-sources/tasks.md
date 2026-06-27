## 1. Planning And Harness

- [x] 1.1 Confirm branch, clean worktree, recent commits, remote sync, and active OpenSpec state.
- [x] 1.2 Create OpenSpec proposal, design, tasks, and harness-development-workflow spec delta.
- [x] 1.3 Synchronize `.harness/allowed_files.md` and `.harness/review_checklist.md` before implementation.
- [x] 1.4 Run internal plan review and classify findings as `fix`, `clarify`, `reject`, or `defer`.
- [x] 1.5 Run Codex independent plan review and classify findings as `fix`, `clarify`, `reject`, or `defer`.
- [x] 1.6 Run `opencode session list` to identify reusable review sessions.
- [x] 1.7 Run OpenCode independent plan review using session reuse rules and classify findings as `fix`, `clarify`, `reject`, or `defer`.
- [x] 1.8 Run `openspec validate consolidate-stage-documentation-sources --strict`.
- [x] 1.9 Stop for explicit user confirmation before implementation.

## 2. Candidate Documentation Changes After Confirmation

- [x] 2.1 Reduce README current-state duplication and keep it as a concise project facade.
- [x] 2.2 Move transient roadmap/current-stage wording out of ARCHITECTURE unless it describes stable runtime boundaries.
- [x] 2.3 Keep PROGRESS history intact while ensuring current next-step guidance reflects the live post-V25 baseline.
- [x] 2.4 Keep HANDOFF limited to next-session safe actions, not duplicate long-term history.
- [x] 2.5 Keep FEATURE_LIST notes acceptance-oriented and remove roadmap narration where redundant.
- [x] 2.6 Update AGENT_RULES or harness workflow docs only where responsibility rules need to be durable.

## 3. Candidate Drift Checks After Confirmation

- [x] 3.1 Refine `scripts/check_stage_docs.ps1` to distinguish current-state sections from historical records.
- [x] 3.2 Add checks for stale current-stage wording that should never appear in README, HANDOFF, Harness, or current PROGRESS guidance.
- [x] 3.3 Keep the script ASCII-safe and avoid fragile false positives against archived OpenSpec history.
- [x] 3.4 Update the existing docs-consistency regression test so it validates the new documentation ownership contract instead of requiring README to carry the full route map.

## 4. Review, Debt Sweep, And Verification

- [x] 4.1 Run focused documentation debt sweep over changed docs and adjacent responsibility statements.
- [x] 4.2 Run `openspec validate --all`.
- [x] 4.3 Run `powershell -ExecutionPolicy Bypass -File scripts/check_stage_docs.ps1`.
- [x] 4.4 Run `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1` if scripts/specs changed.
- [x] 4.5 Run `git diff --check`.
- [x] 4.6 Run final implementation review and triage findings before archive.
