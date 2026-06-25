## 1. Harness And Planning

- [x] 1.1 Confirm branch, worktree, recent commits, and active OpenSpec state.
- [x] 1.2 Create CLI implementation proposal, design, tasks, and spec deltas.
- [x] 1.3 Synchronize `.harness/allowed_files.md` and `.harness/review_checklist.md` before runtime/test edits.
- [x] 1.4 Run internal plan review and OpenSpec validation.
- [x] 1.5 Stop for explicit implementation confirmation.

## 2. TDD: CLI Parser And Command Mapping

- [x] 2.1 Add RED tests for `ask`, `patch`, `patch confirm`, `patch confirm --verify`, `verify`, `status`, and `audit latest` mapping to `ChatService`.
- [x] 2.2 Add RED tests for global `--repo`, `--user-id`, and `--session-id` defaults and overrides.
- [x] 2.3 Add RED tests for output formatting with `trace_id`, `answer`, `related_files`, and `tool_calls`.

## 3. TDD: Safety And Failure Behavior

- [x] 3.1 Add RED tests rejecting invalid verification labels, extra arguments, shell-like syntax, pipes, redirects, and environment assignment before `ChatService`.
- [x] 3.2 Add RED tests rejecting unsafe patch ids before `ChatService`.
- [x] 3.3 Add RED tests for usage/validation exit code `2` and unexpected wrapper failure exit code `1` without raw traceback.

## 4. Implementation

- [x] 4.1 Implement `app/cli.py` with stdlib `argparse`, structured commands, safe validation, and direct `ChatService` call.
- [x] 4.2 Add `repopilot = "app.cli:main"` console script metadata in `pyproject.toml`.
- [x] 4.3 Keep implementation free of new dependencies, HTTP client mode, provider config reads, arbitrary subprocess, and runtime contract changes.

## 5. Docs, Review, And Verification

- [x] 5.1 Update README CLI section from “规划中” to implemented thin CLI only after tests pass.
- [x] 5.2 Update `docs/FEATURE_LIST.json`, `docs/PROGRESS.md`, `HANDOFF_TO_NEXT_CHAT.md`, and long-term specs only for changed owned facts.
- [x] 5.3 Run focused CLI tests and adjacent AgentLoop/API/verification regressions.
- [x] 5.4 Run `openspec validate add-demo-ready-agent-cli --strict` and `openspec validate --all`.
- [x] 5.5 Run `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`.
- [x] 5.6 Run `git diff --check`.
- [x] 5.7 Run internal final review and focused external review before archive.
