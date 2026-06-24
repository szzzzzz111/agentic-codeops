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

- [x] 4.1 Obtain explicit user confirmation and run exactly one complete DeepSeek live gate with no retry or extra diagnostic calls.
- [x] 4.2 Classify outcome from stdout plus evidence paths, not exit code alone; PASS did not occur, and the latest runner-produced failure artifact is retained as trustworthy provider conformance FAIL pause-site evidence.
- [x] 4.3 Verify report hash, tested commit, UTC, profile/model, rubric, 10 cases, 8 calls, hard gates, complete provider contact, metrics, cost and redaction.

## 5. Closeout

- [x] 5.1 Update only durable provider-conformance facts in PROGRESS and concise next-session context in HANDOFF.
- [x] 5.2 Archive only after a valid PASS attestation and all review findings are closed.
- [x] 5.3 If outcome is not PASS, record the pause and stop without archive/merge/push; the current failure artifact may remain only on the current revalidation branch unless the contract is formally reshaped.
- [x] 5.4 On PASS, prepare archive readiness: valid PASS attestation is committed, evidence has been reviewed, and archive/merge verification must run after archive.

## 6. Post-remediation renewed validation

- [x] 6.1 Merge archived `harden-grounded-prompt-injection-live-behavior` remediation back into this revalidation branch.
- [x] 6.2 Mark prior `20260624-110532` live evidence stale for current certification because runtime prompt changed.
- [x] 6.3 Re-run deterministic preflight on the new merged runtime commit.
- [x] 6.4 Obtain explicit user confirmation before exactly one renewed live gate.
- [x] 6.5 Classify renewed live outcome from stdout plus evidence path, and require PASS attestation before archive/merge/push completion.
