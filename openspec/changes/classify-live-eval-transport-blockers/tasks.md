## 1. Planning And Harness

- [x] 1.1 Create high-risk OpenSpec artifacts for transport blocker classification.
- [x] 1.2 Synchronize allowed files and review checklist for the remediation change.
- [x] 1.3 Validate OpenSpec/stage docs/diff and stop for implementation confirmation.

## 2. TDD Implementation

- [ ] 2.1 Add RED tests for redacted transport diagnostic metadata.
- [ ] 2.2 Add RED tests that all-unavailable provider attempts produce transport/integrity blocker with no tracked evidence.
- [ ] 2.3 Add RED tests preserving conformance failure record generation when provider-contact is confirmed.
- [ ] 2.4 Add RED tests for explicit live-network confirmation guard before provider calls.
- [ ] 2.5 Implement minimal evaluator/provider diagnostics and blocker classification.
- [ ] 2.6 Update stdout/report serialization and PowerShell entrypoint behavior without adding live network dependency to default verify.

## 3. Verification And Review

- [ ] 3.1 Run focused evaluator tests and full deterministic verify.
- [ ] 3.2 Run OpenSpec strict/all validation, stage docs checks and `git diff --check`.
- [ ] 3.3 Perform internal review of evidence lifecycle, redaction, shell guard and historical evidence immutability.
- [ ] 3.4 Perform independent adversarial review because evidence lifecycle is high risk.
- [ ] 3.5 Complete focused Stage Debt Sweep over changed evaluator paths and direct dependencies.

## 4. Closeout

- [ ] 4.1 Update durable progress and next-session handoff only with facts owned by this remediation.
- [ ] 4.2 Archive after deterministic verification and all review findings are closed.
- [ ] 4.3 Merge remediation back into the paused revalidation branch; mark old revalidation live evidence stale.
- [ ] 4.4 Stop before any new live provider certification run unless the user explicitly confirms network-capable execution.
