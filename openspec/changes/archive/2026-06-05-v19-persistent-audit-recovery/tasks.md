## 1. OpenSpec And Harness

- [x] 1.1 Create V19 `stage_planning.md`, `proposal.md`, `design.md`, `tasks.md`, and spec deltas.
- [x] 1.2 Add long-term `persistent-audit-recovery` spec draft.
- [x] 1.3 Update `.harness/allowed_files.md` for V19 runtime, docs, tests, and optional process-doc boundaries.
- [x] 1.4 Update `.harness/review_checklist.md` with V19 audit/recovery and Stage Debt Sweep gates.
- [x] 1.5 Validate `v19-persistent-audit-recovery` OpenSpec change.

## 2. Tests

- [x] 2.1 Add audit store tests for schema, scoping, ordering, default limit, missing-store no-create, and unlimited retention behavior.
- [x] 2.2 Add redaction/capping tests proving full diff, stdout/stderr, Evidence Pack, provider content, secrets, DB paths, and local absolute paths are not persisted.
- [x] 2.3 Add AgentLoop tests for trace, patch, verification, and long task audit event recording.
- [x] 2.4 Add recovery/status routing tests proving no repo RAG call, no mutation, and unchanged `/chat` contract.
- [x] 2.5 Add audit write failure test proving primary chat behavior remains successful.

## 3. Implementation

- [x] 3.1 Implement `app/audit/store.py` with repo-local SQLite, scoped queries, and no-create read mode.
- [x] 3.2 Implement `app/audit/manager.py` with redacted event writers and recovery query helpers.
- [x] 3.3 Hook AgentLoop trace envelope persistence.
- [x] 3.4 Hook patch attempt, verification result, and long task event persistence.
- [x] 3.5 Implement read-only audit recovery/status intent and answer formatting.

## 4. Docs And Verification

- [x] 4.1 Update README, ARCHITECTURE, PROGRESS, FEATURE_LIST, and HANDOFF for V19.
- [x] 4.2 Run targeted pytest for V19 audit/recovery.
- [x] 4.3 Run `openspec validate v19-persistent-audit-recovery` and `openspec validate --all`.
- [x] 4.4 Run `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`.
- [x] 4.5 Run `git diff --check`.
- [x] 4.6 Run Stage Debt Sweep and record evidence in durable docs and review checklist.
