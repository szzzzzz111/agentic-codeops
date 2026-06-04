## 1. Harness

- [x] 1.1 Update `.harness/allowed_files.md` for V18.
- [x] 1.2 Update `.harness/review_checklist.md` with V18 gates.
- [x] 1.3 Validate `v18-patch-verify-loop` OpenSpec change.

## 2. Tests

- [x] 2.1 Add parser tests for legal combination confirmation, apply-only compatibility, missing label, unsafe label, and unsupported label.
- [x] 2.2 Add AgentLoop tests for route priority, apply-then-verify order, independent verification context, and no-verify-on-apply-failure.
- [x] 2.3 Add `/chat` contract tests for successful loop and invalid combination rejection.

## 3. Implementation

- [x] 3.1 Implement strict combination confirmation parsing.
- [x] 3.2 Add AgentLoop Patch + Verify Loop orchestration before pure verification intent.
- [x] 3.3 Format combined apply/verify answers and preserve safe tool call summaries.

## 4. Docs And Verification

- [x] 4.1 Update README, ARCHITECTURE, PROGRESS, FEATURE_LIST, and HANDOFF.
- [x] 4.2 Run targeted pytest for V18.
- [x] 4.3 Run `openspec validate v18-patch-verify-loop` and `openspec validate --all`.
- [x] 4.4 Run `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`.
- [x] 4.5 Run `git diff --check`.
