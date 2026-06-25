## 1. Harness And Planning

- [x] 1.1 Confirm branch, worktree, recent commits, and active OpenSpec state.
- [x] 1.2 Create V24 CLI Capability Surface proposal, design, tasks, and spec deltas.
- [x] 1.3 Synchronize `.harness/allowed_files.md` and `.harness/review_checklist.md` before runtime/test edits.
- [x] 1.4 Record internal plan review, Codex independent plan review, OpenCode independent plan review, and finding triage.
- [x] 1.5 Run `openspec validate polish-demo-cli-capability-surface --strict` and `openspec validate --all`.

## 2. TDD: CLI Surface

- [x] 2.1 Add RED CLI tests for exact `patch` mapping to `create patch: <request>`.
- [x] 2.2 Add RED CLI tests for runtime-compatible patch id validation boundaries.
- [x] 2.3 Add RED CLI tests for human-readable output sections based on public response fields.
- [x] 2.4 Add or update adjacent tests proving `create patch:` triggers existing patch proposal intent and ChatService message transport remains intact.
- [x] 2.5 Implement the smallest CLI changes to pass the RED tests.

## 3. Workflow Skill Hardening

- [x] 3.1 Update Codex planning/review workflow skills with plan-level internal, Codex, and OpenCode review gates.
- [x] 3.2 Add a focused OpenCode plan-review workflow entry or skill.
- [x] 3.3 Add deterministic checks or tests for required skill wording, including OpenCode session reuse and timeout handling.

## 4. Docs And Specs

- [x] 4.1 Update README walkthrough and roadmap without claiming real model patch authoring or promotion is implemented.
- [x] 4.2 Update ARCHITECTURE, FEATURE_LIST, PROGRESS, HANDOFF, and long-term specs for changed owned facts.
- [x] 4.3 Keep Verified Patch Promotion as V25/backlog only.

## 5. Review And Verification

- [x] 5.1 Run focused CLI tests and adjacent regressions.
- [x] 5.2 Run workflow/skill wording checks.
- [x] 5.3 Run full `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`.
- [x] 5.4 Run `git diff --check`.
- [x] 5.5 Run internal final implementation review and focused external review.
- [x] 5.6 Perform Stage Debt Sweep over changed paths and directly dependent older paths.
