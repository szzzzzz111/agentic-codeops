## 1. Harness And Planning

- [x] 1.1 Create and internally review the high-risk OpenSpec change.
- [x] 1.2 Synchronize allowed files and review checklist before implementation.

## 2. TDD Evaluator Foundations

- [x] 2.1 Add failing tests for required environment SKIP, profile mismatch, exit codes and clean-tree preflight.
- [x] 2.2 Implement the versioned DeepSeek profile, environment validation and runner result model.
- [x] 2.3 Add failing tests and implementation for call budgets, deadlines, metrics gates and cost calculation.

## 3. TDD Fixtures, Rubric And Safety

- [x] 3.1 Add the fixed fixture/rubric dataset and failing tests for quality `x/5`, no-answer and prompt-injection gates.
- [x] 3.2 Implement deterministic rubric scoring without persisting raw model content.
- [x] 3.3 Add failing tests and implementation for retrieval/EvidencePack/payload secret filtering.

## 4. TDD Live Component Runners

- [x] 4.1 Add failing tests and implementation for the fresh-subprocess `/chat` default-wiring smoke.
- [x] 4.2 Add failing tests and implementation for Grounded Answer and Long Task Planner live cases.
- [x] 4.3 Add failing tests and implementation for temporary-repo PatchManager injection without apply.

## 5. Reports And Entry Point

- [x] 5.1 Add failing tests and implementation for allowlist local reports, SHA-256 and PASS-only tracked attestation.
- [x] 5.2 Add the thin PowerShell live entry point without changing default verify.
- [x] 5.3 Add deterministic integration tests for SKIP, FAIL and simulated PASS orchestration.

## 6. Verification And Review

- [x] 6.1 Run focused evaluator and adjacent provider/retrieval/Planner/Patch/API tests.
- [x] 6.2 Run full deterministic verification, OpenSpec validation, stage checks and `git diff --check`.
- [x] 6.3 Perform final internal review, independent adversarial external review and focused Stage Debt Sweep.
- [x] 6.4 Commit the reviewed evaluator implementation on a clean tracked tree.

## 7. Reshaped Tracked Evidence Contract

- [ ] 7.1 Add failing tests for the exact evaluated-failure allowlist schema, sorted known conformance gates, forbidden content and PASS/FAIL evidence exclusivity.
- [ ] 7.2 Add failing tests that distinguish complete conformance FAIL from SKIP and evaluation integrity failure, including every single-case and whole-run call-count gate.
- [ ] 7.3 Implement exclusive-create local report, PASS-only attestation and tracked evaluated-failure record without changing live exit codes or hard gates.
- [ ] 7.4 Add simulated PASS, trustworthy FAIL and integrity-failure orchestration tests.

## 8. Reshaped Verification And Review

- [ ] 8.1 Run focused evaluator tests, adjacent provider/runtime regressions and full deterministic verify.
- [ ] 8.2 Perform internal review, independent adversarial external review and focused Stage Debt Sweep against the reshaped contract.
- [ ] 8.3 Close all findings and commit the final evaluator implementation on a clean tracked tree.

## 9. Final Live Evidence And Closeout

- [ ] 9.1 Run the real DeepSeek live gate against the final committed evaluator; do not derive tracked evidence from historical reports.
- [ ] 9.2 Commit either a PASS-only attestation or a valid evaluated-failure record; SKIP/integrity failures remain blockers.
- [ ] 9.3 Perform final evidence review against the local report hash, evaluator commit, provider/model, rubric and gate results.
- [ ] 9.4 Archive, integrate and push only after evaluator readiness evidence and all review findings are closed.
