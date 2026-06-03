## 1. Harness And OpenSpec

- [x] 1.1 Create V17 stage planning, OpenSpec proposal, design, spec deltas, and tasks.
- [x] 1.2 Update `.harness/allowed_files.md` for the V17 writable boundary.
- [x] 1.3 Update `.harness/review_checklist.md` for verification intent, command whitelist, permission context, ToolExecutor execution, output redaction, contract, and non-goal gates.
- [x] 1.4 Run `openspec validate v17-verification-runner`.

## 2. Tests

- [x] 2.1 Add failing verification runner unit tests for parser labels, whitelist lookup, repo path boundary, subprocess timeout, missing command handling, output truncation, path redaction, and non-zero exit summaries.
- [x] 2.2 Add failing PermissionPolicy / ApprovalGate tests for `verification_run`, explicit verification context, normal `ask` blocking, and invalid whitelist denial.
- [x] 2.3 Add failing AgentLoop tests proving V17 priority: Memory, Long Task, Assistant Control Surface, Patch, Verification, capability-status, repo_search/chat_only.
- [x] 2.4 Add failing `/chat` contract tests proving verification requests keep top-level fields, do not call repo_rag, do not expose full stdout/stderr, and do not accept arbitrary shell syntax.

## 3. Implementation

- [x] 3.1 Add `app/verification/` with verification intent parser, command whitelist registry, result dataclass, output summarizer, and subprocess runner.
- [x] 3.2 Register `verification_run` tool metadata and update `ToolInvocationContext` usage without adding new permission statuses.
- [x] 3.3 Add `ToolExecutor.verification_run(...)` as the only runtime verification execution path.
- [x] 3.4 Integrate Verification intent into AgentLoop with fixed priority after Patch and before capability-status/repo_search.
- [x] 3.5 Add V17 capability-status wording while keeping V18+ as non-goals.

## 4. Docs And Verification

- [x] 4.1 Update README, ARCHITECTURE, PROGRESS, FEATURE_LIST, and HANDOFF for V17 behavior and non-goals.
- [x] 4.2 Run `openspec validate v17-verification-runner`.
- [x] 4.3 Run `openspec validate --all`.
- [x] 4.4 Run `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`.
- [x] 4.5 Run `git diff --check`.
- [x] 4.6 Complete implementation self-review before external review or archive.
