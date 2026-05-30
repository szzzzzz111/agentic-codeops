## 1. Harness And OpenSpec

- [x] 1.1 Create V14 OpenSpec proposal, design, spec deltas, and tasks.
- [x] 1.2 Update `.harness/allowed_files.md` for the V14 writable boundary.
- [x] 1.3 Update `.harness/review_checklist.md` for Long Task routing, SQLite, ReAct trace, quota/archive, provider fallback, subagent/worktree non-goals, and contract gates.
- [x] 1.4 Run `openspec validate v14-long-task-react-subagents`.

## 2. Tests

- [x] 2.1 Add failing Long Task store tests for SQLite init, V13-compatible repo_key, user+repo isolation, quota/list/archive, reopen retry round, and redaction.
- [x] 2.2 Add failing planner/parser tests for natural language commands, stage_planning trigger, task type templates, provider JSON fallback, and text limits.
- [x] 2.3 Add failing AgentLoop tests proving Long Task commands are handled before router/keyword, creation does not call repo_rag, resume calls repo_rag through permission/approval, no-result blocks, and failures pause/fail by attempt count.
- [x] 2.4 Add failing `/chat` contract tests proving Long Task does not add public fields or leak scratch/provider output/local paths.

## 3. Implementation

- [x] 3.1 Add Long Task data structures, constants, command parser, task type planner, provider-assisted planning boundary, and sanitized formatting helpers.
- [x] 3.2 Add SQLiteLongTaskStore using `.repopilot/tasks.sqlite3` and V13 repo_key normalization.
- [x] 3.3 Add LongTaskManager for create/list/status/pause/resume/supplement/reopen/archive and quota/state transition orchestration.
- [x] 3.4 Integrate LongTaskManager into AgentLoop before RequestRouter while preserving Memory, PermissionPolicy, ApprovalGate, ToolExecutor, Evidence Pack and `/chat` boundaries.
- [x] 3.5 Preserve subagent/worktree as metadata only; do not implement real subagent dispatch or git/worktree actions.

## 4. Docs And Verification

- [x] 4.1 Update README, ARCHITECTURE, PROGRESS, FEATURE_LIST, and HANDOFF for V14 behavior and non-goals.
- [x] 4.2 Run `openspec validate v14-long-task-react-subagents`.
- [x] 4.3 Run `openspec validate --all`.
- [x] 4.4 Run `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`.
- [x] 4.5 Run `git diff --check`.
- [x] 4.6 Complete implementation self-review before archive.
