## 1. Harness

- [x] 1.1 Update `.harness/allowed_files.md` for V9 planning and implementation scope.
- [x] 1.2 Update `.harness/review_checklist.md` with V9-specific review checks.

## 2. Tests

- [x] 2.1 Add failing tests for deterministic embedding provider behavior.
- [x] 2.2 Add failing tests that the embedding provider returns fixed-dimension vectors with a stable vector format and no external calls.
- [x] 2.3 Add failing tests for embedding retrieval citation safety.
- [x] 2.4 Add failing tests for hybrid fusion deduplication and stable ranking.
- [x] 2.5 Add failing tests that `/chat` preserves the existing top-level contract.
- [x] 2.6 Add failing tests for capability-status questions about external vector stores and future LLM features.

## 3. Implementation

- [x] 3.1 Implement the smallest embedding provider boundary and deterministic default provider.
- [x] 3.2 Implement repo-local embedding retrieval over allowed text chunks.
- [x] 3.3 Implement deterministic hybrid fusion over lexical and embedding retrieval results.
- [x] 3.4 Wire `ToolExecutor(repo_rag)` and `AgentLoop` to use hybrid retrieval after V7 permission/approval checks.
- [x] 3.5 Preserve lexical retrieval as a first-class channel and keep citation paths relative.

## 4. Docs and Feature List

- [x] 4.1 Update `README.md` and `docs/ARCHITECTURE.md` with V9 current capability and non-goals.
- [x] 4.2 Update `docs/PROGRESS.md` and `HANDOFF_TO_NEXT_CHAT.md` with V9 status and route split.
- [x] 4.3 Update `docs/FEATURE_LIST.json` with a V9 acceptance item.

## 5. Validation

- [x] 5.1 Run `openspec validate v9-embedding-hybrid-search`.
- [x] 5.2 Run `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`.
- [x] 5.3 Run `git diff --check`.
