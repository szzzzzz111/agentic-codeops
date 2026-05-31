## 1. Harness And OpenSpec

- [x] 1.1 Create V15 OpenSpec proposal, design, spec deltas, and tasks.
- [x] 1.2 Update `.harness/allowed_files.md` for the V15 writable boundary.
- [x] 1.3 Update `.harness/review_checklist.md` for Assistant Control Surface routing, read-only summaries, DB non-initialization, redaction, contract, and non-goal gates.
- [x] 1.4 Run `openspec validate v15-assistant-control-surface`.

## 2. Tests

- [x] 2.1 Add failing Assistant Control Surface unit tests for trigger parsing, answer format, status aggregation, unavailable repo handling, and DB non-initialization.
- [x] 2.2 Add failing AgentLoop tests proving Assistant Control Surface runs after Memory/Long Task commands, before capability-status/repo_search, and never calls `repo_rag`.
- [x] 2.3 Add failing `/chat` contract tests proving control surface responses keep existing top-level fields and do not leak paths, DB names, memory values, scratch, provider output, or Evidence Pack.

## 3. Implementation

- [x] 3.1 Add Assistant Control Surface module with trigger parser, status data structures, read-only status collector, and answer formatter.
- [x] 3.2 Add read-only Memory summary support that counts PREF/LTM/STM without creating `.repopilot` directories or SQLite DB files.
- [x] 3.3 Add read-only Long Task summary support that lists count and recent task metadata without exposing scratch/ReAct trace or creating DB files.
- [x] 3.4 Integrate Assistant Control Surface into AgentLoop with the fixed priority: Memory command, Long Task command, Assistant Control Surface, capability-status, repo_search/chat_only.

## 4. Docs And Verification

- [x] 4.1 Update README, ARCHITECTURE, PROGRESS, FEATURE_LIST, and HANDOFF for V15 behavior and non-goals.
- [x] 4.2 Run `openspec validate v15-assistant-control-surface`.
- [x] 4.3 Run `openspec validate --all`.
- [x] 4.4 Run `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`.
- [x] 4.5 Run `git diff --check`.
- [x] 4.6 Complete implementation self-review before archive.
