## 1. Harness And OpenSpec

- [x] 1.1 Create V11 OpenSpec proposal, design, spec deltas, and tasks.
- [x] 1.2 Update `.harness/allowed_files.md` for the V11 writable boundary.
- [x] 1.3 Update `.harness/review_checklist.md` for V11 plan, dependency, provider, citation, and verification review gates.
- [x] 1.4 Run `openspec validate v11-grounded-answer-model-provider-boundary`.

## 2. Tests

- [x] 2.1 Add failing provider tests for fake provider stability and OpenAI-compatible provider request/error handling with mock transport.
- [x] 2.2 Add failing grounded answer tests for evidence input mapping, citation validation, fallback behavior, and provider audit redaction.
- [x] 2.3 Add failing AgentLoop tests proving `/chat` answers use grounded answer when evidence exists and fallback when evidence/provider validation fails.
- [x] 2.4 Add failing API contract tests proving `/chat` top-level fields and `tool_calls` do not expose prompt, evidence pack, API key, model output, or internal trace.
- [x] 2.5 Add failing docs tests for V11 route map and non-goals.

## 3. Implementation

- [x] 3.1 Add `app/providers` model provider boundary, fake provider, OpenAI-compatible provider, and environment-based provider factory.
- [x] 3.2 Add `app/answering` grounded answer structures, citation validation, fallback, and audit summary logic.
- [x] 3.3 Integrate grounded answer into `AgentLoop` after successful `repo_rag` evidence pack creation.
- [x] 3.4 Promote `httpx` to runtime dependency while keeping default verification offline.
- [x] 3.5 Preserve existing permission, approval, safe file tool, hybrid retrieval, Evidence Pack, and `/chat` contract boundaries.

## 4. Docs And Verification

- [x] 4.1 Update README, ARCHITECTURE, PROGRESS, FEATURE_LIST, and HANDOFF for V11 behavior and next-step route map.
- [x] 4.2 Run `openspec validate v11-grounded-answer-model-provider-boundary`.
- [x] 4.3 Run `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`.
- [x] 4.4 Run `git diff --check`.
- [x] 4.5 Complete implementation self-review before archive.
