## 1. Harness And Planning

- [x] 1.1 Create the medium-risk OpenSpec change and synchronize allowed files.
- [x] 1.2 Internally review proposal, design, delta specs, test plan, and non-goals.

## 2. TDD Regression Coverage

- [x] 2.1 Add a failing Kernel test requiring patch capability-status to include V19-V23 truth and current non-goals.
- [x] 2.2 Add a failing `/chat` contract test for the corrected patch capability-status response.
- [x] 2.3 Add a characterization test proving shared Model Provider environment configuration does not wire the default patch provider.

## 3. Minimal Runtime And Documentation Fix

- [x] 3.1 Update the deterministic patch capability-status answer without changing routing or execution behavior.
- [x] 3.2 Correct README and ARCHITECTURE provider wiring claims.
- [x] 3.3 Sync long-term specs, PROGRESS, and HANDOFF with the implemented truth boundary.
- [x] 3.4 Remove the stale process-only HANDOFF markers from the deterministic stage-docs checker.

## 4. Verification And Review

- [x] 4.1 Run focused Kernel/API tests and OpenSpec strict validation.
- [x] 4.2 Run full `scripts/verify.ps1`, `openspec validate --all`, and `git diff --check`.
- [x] 4.3 Perform formal internal review and focused Stage Debt Sweep after final runtime/test changes.
- [x] 4.4 Obtain focused external review of capability truth and provider non-goals, then close valid findings.
