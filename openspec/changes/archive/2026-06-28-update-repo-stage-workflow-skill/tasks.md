## 1. Planning And Harness

- [x] 1.1 Confirm branch, worktree, recent commits, remote sync, and active OpenSpec state.
- [x] 1.2 Create OpenSpec proposal, tasks, and harness-development-workflow spec delta.
- [x] 1.3 Synchronize `.harness/allowed_files.md` and `.harness/review_checklist.md` before implementation edits.
- [x] 1.4 Classify risk and define review/verification depth.

## 2. Workflow Skill Update

- [x] 2.1 Update `repo-stage-workflow` so OpenSpec owns requirement/design/task/spec baseline.
- [x] 2.2 Update `repo-stage-workflow` so Superpowers-style execution discipline owns reading specs, isolation, TDD, verification, review, finish, and skill self-checks.
- [x] 2.3 Add the change-loop rule: requirement or design drift returns to OpenSpec before implementation resumes.
- [x] 2.4 Keep wording process-only and avoid describing skills as RepoPilot runtime capability.

## 3. Current-State Drift Correction

- [x] 3.1 Correct `docs/PROGRESS.md` post-merge/push wording for repo mutation locking.
- [x] 3.2 Correct `HANDOFF_TO_NEXT_CHAT.md` so the next session starts from live-state checks instead of stale closeout instructions.
- [x] 3.3 Update the docs consistency assertion so active OpenSpec changes are allowed during a valid stage.

## 4. Review And Verification

- [x] 4.1 Run internal review over scope, roadmap truth, skill clarity, and docs ownership.
- [x] 4.2 Perform focused Stage Debt Sweep over changed workflow docs and current-state docs.
- [x] 4.3 Run `openspec validate update-repo-stage-workflow-skill --strict`.
- [x] 4.4 Run `openspec validate --all`.
- [x] 4.5 Run deterministic stage docs / skill checks or full `scripts/verify.ps1` when practical.
- [x] 4.6 Run `git diff --check`.
- [x] 4.7 Archive the OpenSpec change after validation and review are complete.
