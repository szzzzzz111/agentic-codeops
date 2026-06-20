## 1. Harness And Planning

- [x] 1.1 Create the medium-risk OpenSpec change and synchronize allowed files.
- [x] 1.2 Internally review proposal, design, delta spec, test plan, and non-goals.

## 2. TDD Regression Coverage

- [x] 2.1 Add a failing Kernel test proving V11 status reflects V12/V13 current truth.
- [x] 2.2 Add a failing Kernel/API test proving V12 status reflects V13 current truth and preserves real non-goals.

## 3. Minimal Runtime And Documentation Fix

- [x] 3.1 Update only the V11/V12 deterministic capability-status constants.
- [x] 3.2 Sync the long-term agent-loop spec and current stage docs without rewriting historical stage sections.

## 4. Verification And Review

- [x] 4.1 Run focused Kernel/API tests and OpenSpec strict validation.
- [x] 4.2 Run full `scripts/verify.ps1`, `openspec validate --all`, and `git diff --check`.
- [x] 4.3 Perform formal internal review and focused Stage Debt Sweep after final runtime/test changes.
- [x] 4.4 Obtain focused external review and close valid findings.
