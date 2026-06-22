## 1. Harness And Planning

- [x] 1.1 Create the high-risk OpenSpec change and synchronize allowed files and review checklist.
- [x] 1.2 Internally review proposal, design, delta specs, TDD plan, failure behavior, and Harness boundaries.

## 2. TDD Provider Request Contract

- [x] 2.1 Add failing tests for backward-compatible defaults, unknown modes, structured instruction validation, and zero HTTP calls on invalid requests.
- [x] 2.2 Implement output modes, `StructuredOutputInstruction`, validation, and stable request-validation errors.
- [x] 2.3 Add failing tests and implementation for text/JSON payload separation, JSON object response validation, and explicit thinking configuration.

## 3. TDD Callers And Metrics

- [x] 3.1 Add failing Planner/Patch tests for single-source JSON instructions and provider-status preflight.
- [x] 3.2 Update Planner/Patch callers while preserving their business schema, citation, path, and diff validation.
- [x] 3.3 Add failing tests and implementation for response-local metrics, finish-reason handling, missing usage compatibility, and audit redaction.

## 4. Regression, Documentation, And Verification

- [x] 4.1 Run focused provider, Planner, Patch, Grounded Answer, AgentLoop, API, and persistent-audit tests.
- [x] 4.2 Update only durable specs/docs whose owned provider-contract facts changed.
- [x] 4.3 Run full `scripts/verify.ps1`, OpenSpec strict/all validation, stage checks, and `git diff --check`.
- [x] 4.4 Perform final internal review, independent adversarial external review, focused Stage Debt Sweep, and close all blocking findings.
- [x] 4.5 Confirm archive/integration readiness; archive and integration follow the stage closeout workflow before any live-eval change is created.
