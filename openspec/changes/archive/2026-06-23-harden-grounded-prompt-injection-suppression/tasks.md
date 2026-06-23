## 1. Harness And Planning

- [x] 1.1 Synchronize allowed files and review checklist for the medium-risk remediation.
- [x] 1.2 Complete internal plan review and strict OpenSpec validation before implementation.

## 2. TDD Prompt Contract

- [x] 2.1 Add failing tests proving grounded-text instruction requires silent suppression of evidence commands and their marker/token targets.
- [x] 2.2 Add failing tests proving the instruction explicitly forbids clarification/refusal from acknowledging or reproducing an injected marker/token and retains the exact citation footer.
- [x] 2.3 Add prompt-contract coverage preserving an explicitly queried same-name repository identifier.
- [x] 2.4 Add regression assertions that JSON object mode, evidence envelope and existing citation instruction remain unchanged.

## 3. Minimal Runtime Remediation

- [x] 3.1 Make the smallest grounded-text system prompt change that satisfies the silent suppression contract.
- [x] 3.2 Keep output validation, post-processing, provider metrics, default wiring and public API behavior unchanged.

## 4. Verification And Review

- [x] 4.1 Run focused Model Provider/Grounded Answer/AgentLoop/API tests.
- [x] 4.2 Run full deterministic verification, OpenSpec validation and `git diff --check`.
- [x] 4.3 Perform internal review, focused independent external review and Stage Debt Sweep.
- [x] 4.4 Close all blocking findings and rerun affected verification.

## 5. Archive And Eval Handoff

- [x] 5.1 Update only durable docs whose owned facts changed and confirm archive readiness.
- [x] 5.2 Record that merge and push occur only after archive verification.
- [x] 5.3 Record the eval-resume handoff, including evidence invalidation and the prohibition on running live gate inside this remediation.
