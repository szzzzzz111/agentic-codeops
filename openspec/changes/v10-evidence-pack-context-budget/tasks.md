## 1. Harness And Plan Review

- [x] 1.1 Create V10 OpenSpec proposal, design, spec delta, and tasks.
- [x] 1.2 Update `.harness/allowed_files.md` for the V10 writable boundary.
- [x] 1.3 Update `.harness/review_checklist.md` for V10 plan and implementation review gates.
- [x] 1.4 Run `openspec validate v10-evidence-pack-context-budget`.
- [x] 1.5 Stop for user plan/review confirmation before writing runtime code or tests.
- [x] 1.6 Resolve review findings in design/spec/tasks before implementation.

## 2. Tests

- [x] 2.1 Add failing tests for Evidence Pack item shape, stable evidence ids, relative citation paths, and no absolute path leakage.
- [x] 2.2 Add failing tests for context budget included, omitted, truncated, and budget-used fields.
- [x] 2.3 Add failing tests proving Evidence Pack audit summary is internal and `/chat` top-level contract remains unchanged.
- [x] 2.4 Add failing tests for empty retrieval results and tool error behavior.
- [x] 2.5 Add failing tests confirming V10 does not claim grounded answer, model provider, rerank, memory, or context compression.
- [x] 2.6 Add failing tests proving `ToolExecutionResult.evidence_pack` does not enter `call_summary()`, `/chat.tool_calls`, or `/chat` top-level fields.
- [x] 2.7 Add a route-map consistency check that rejects old `V10 = Query Rewrite / Rerank / Context Budget` wording.

## 3. Implementation

- [x] 3.1 Add a lightweight `app/rag/evidence.py` module for Evidence Pack and context budget structures.
- [x] 3.2 Build Evidence Pack from repo RAG results without reading files directly or changing retrieval ordering.
- [x] 3.3 Integrate Evidence Pack summary into `ToolExecutionResult` / `ToolExecutor.search_repo_rag` internal audit output.
- [x] 3.4 Record Evidence Pack summary in `AgentLoop` internal trace without adding `/chat` required top-level fields.
- [x] 3.5 Preserve existing permission, approval, safe file tool, and hybrid retrieval boundaries.

## 4. Docs And Verification

- [x] 4.1 Update README, ARCHITECTURE, PROGRESS, FEATURE_LIST, and HANDOFF to describe actual V10 behavior after implementation.
- [x] 4.2 Run `openspec validate v10-evidence-pack-context-budget`.
- [x] 4.3 Run `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`.
- [x] 4.4 Run `git diff --check`.
- [x] 4.5 Complete internal self-review and stop for external/user review before archive.
- [x] 4.6 Confirm design/spec/tasks field names match before implementation-complete review.
