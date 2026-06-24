## 1. Planning And Harness

- [x] 1.1 Create and internally review the high-risk revalidation OpenSpec artifacts.
- [x] 1.2 Synchronize allowed files and review checklist before any live execution.
- [x] 1.3 Commit the reviewed planning baseline on an otherwise clean tracked tree.

## 2. Deterministic Preflight

- [x] 2.1 Run focused evaluator tests and full deterministic `scripts/verify.ps1`.
- [x] 2.2 Run OpenSpec strict/all validation, stage checks and `git diff --check`.
- [x] 2.3 Confirm the ignored live configuration is complete without printing values or sending diagnostic model calls.

## 3. Formal Review

- [x] 3.1 Perform internal review of clean-commit identity, evidence exclusivity, no-retry budget and historical evidence immutability.
- [x] 3.2 Perform independent adversarial review of the revalidation plan and preflight evidence.
- [x] 3.3 Close all findings and commit the final pre-live documentation state.

## 4. Live Conformance Gate

- [ ] 4.1 Obtain explicit user confirmation and run exactly one complete DeepSeek live gate with no retry or extra diagnostic calls.
- [ ] 4.2 Classify outcome from stdout plus evidence paths, not exit code alone; on PASS commit the PASS-only attestation, while a valid conformance FAIL may commit only pause-site failure evidence on the current branch and FAIL/SKIP/ERROR/integrity-blocked outcomes pause without runtime changes.
- [ ] 4.3 Verify report hash, tested commit, UTC, profile/model, rubric, 10 cases, 8 calls, hard gates, metrics, cost and redaction.

## 5. Closeout

- [ ] 5.1 Update only durable provider-conformance facts in PROGRESS and concise next-session context in HANDOFF.
- [ ] 5.2 Archive only after a valid PASS attestation and all review findings are closed.
- [ ] 5.3 If outcome is not PASS, record the pause and stop without archive/merge/push; a valid FAIL record may remain only on the current revalidation branch unless the contract is formally reshaped.
- [ ] 5.4 On PASS, verify archive sync preserves all existing requirements, then run archive/merge verification, integrate into `main`, push and write one final handoff.
