## 1. Harness And Planning

- [x] 1.1 Synchronize allowed files and review checklist for the medium-risk remediation.
- [x] 1.2 Complete internal plan review and strict OpenSpec validation before implementation.

## 2. TDD Prompt Contract

- [ ] 2.1 Add failing tests proving grounded-text instruction requires silent suppression of evidence commands and their marker/token targets.
- [ ] 2.2 Add failing tests proving the instruction explicitly forbids clarification/refusal from acknowledging or reproducing the attack target and retains the exact citation footer.
- [ ] 2.3 Add regression coverage proving an explicitly queried same-name repository identifier remains answerable.
- [ ] 2.4 Add regression assertions that JSON object mode, evidence envelope and existing citation instruction remain unchanged.

## 3. Minimal Runtime Remediation

- [ ] 3.1 Make the smallest grounded-text system prompt change that satisfies the silent suppression contract.
- [ ] 3.2 Keep output validation, post-processing, provider metrics, default wiring and public API behavior unchanged.

## 4. Verification And Review

- [ ] 4.1 Run focused Model Provider/Grounded Answer/AgentLoop/API tests.
- [ ] 4.2 Run full deterministic verification, OpenSpec validation and `git diff --check`.
- [ ] 4.3 Perform internal review, focused independent external review and Stage Debt Sweep.
- [ ] 4.4 Close all blocking findings and rerun affected verification.

## 5. Archive And Eval Handoff

- [ ] 5.1 Update only durable docs whose owned facts changed and archive the remediation.
- [ ] 5.2 Merge and push the remediation after archive verification.
- [ ] 5.3 Resume `add-live-model-provider-eval`, invalidate old evidence and rerun its full workflow; do not run live gate inside this remediation.
