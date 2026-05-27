## 1. Harness And OpenSpec

- [x] 1.1 Create V12 OpenSpec proposal, design, spec deltas, and tasks.
- [x] 1.2 Update `.harness/allowed_files.md` for the V12 writable boundary.
- [x] 1.3 Update `.harness/review_checklist.md` for V12 rewrite/rerank, Evidence Pack, citation, and verification gates.
- [x] 1.4 Run `openspec validate v12-query-rewrite-rerank`.

## 2. Tests

- [x] 2.1 Add failing deterministic rewrite tests for original variant, stable ids, template order, max variants, dedup, missing terms fallback, and provider error fallback.
- [x] 2.2 Add failing rerank tests for stable ordering, original/path/symbol/exact priority, max result selection, no extra threshold, and fallback.
- [x] 2.3 Add failing integration tests for AgentLoop multi-query rewrite, retrieval merge, rerank, Evidence Pack, and grounded answer flow.
- [x] 2.4 Add failing contract tests proving `/chat` does not expose rewrite/rerank internals.
- [x] 2.5 Add failing capability status tests for deterministic rewrite/rerank implemented and real LLM rewrite/rerank not implemented.

## 3. Implementation

- [x] 3.1 Add query rewrite structures and deterministic provider.
- [x] 3.2 Add repo result merge and deterministic rerank structures/provider.
- [x] 3.3 Integrate rewrite, multi-query retrieval, merge, and rerank into `ToolExecutor.search_repo_rag`.
- [x] 3.4 Integrate rewrite/rerank audit summaries into `AgentLoop` internal trace.
- [x] 3.5 Preserve existing permission, approval, safe file tool, Evidence Pack, grounded answer, and `/chat` contract boundaries.

## 4. Docs And Verification

- [x] 4.1 Update README, ARCHITECTURE, PROGRESS, FEATURE_LIST, and HANDOFF for V12 behavior and next-step route map.
- [x] 4.2 Run `openspec validate v12-query-rewrite-rerank`.
- [x] 4.3 Run `openspec validate --all`.
- [x] 4.4 Run `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`.
- [x] 4.5 Run `git diff --check`.
- [x] 4.6 Complete implementation self-review before external review/archive.
