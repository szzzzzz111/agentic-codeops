## 1. Harness And OpenSpec

- [x] 1.1 Create V13 OpenSpec proposal, design, spec deltas, and tasks.
- [x] 1.2 Update `.harness/allowed_files.md` for the V13 writable boundary.
- [x] 1.3 Update `.harness/review_checklist.md` for V13 memory, SQLite, audit, command parsing, and contract gates.
- [x] 1.4 Run `openspec validate v13-memory`.

## 2. Tests

- [x] 2.1 Add failing memory store tests for SQLite init, upsert overwrite, list/delete, user/repo/session isolation, repo_key normalization, and audit redaction.
- [x] 2.2 Add failing parser tests for full-width/half-width colons, Chinese/English commands, key/value notes, kind classification, overwrite, and delete matching.
- [x] 2.3 Add failing AgentLoop tests for memory command confirmation, no repo_rag on command, memory read audit on normal search, and memory failure fallback.
- [x] 2.4 Add failing `/chat` contract tests proving memory does not add public fields or leak local paths.

## 3. Implementation

- [x] 3.1 Add Memory data structures, repo_key normalization, SQLiteMemoryStore, and InMemorySessionMemoryStore.
- [x] 3.2 Add MemoryManager command parsing, read/write/delete orchestration, and sanitized audit summaries.
- [x] 3.3 Pass `user_id` and `session_id` through ChatService, CodeAgent, and AgentLoopRequest.
- [x] 3.4 Integrate memory command handling and normal-request memory summaries into AgentLoop.
- [x] 3.5 Preserve permission, approval, ToolExecutor, Evidence Pack, grounded answer, and `/chat` contract boundaries.

## 4. Docs And Verification

- [x] 4.1 Update `.gitignore`, README, ARCHITECTURE, PROGRESS, FEATURE_LIST, and HANDOFF for V13 behavior and next-step route map.
- [x] 4.2 Run `openspec validate v13-memory`.
- [x] 4.3 Run `openspec validate --all`.
- [x] 4.4 Run `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`.
- [x] 4.5 Run `git diff --check`.
- [x] 4.6 Complete implementation self-review before archive.
