## 1. Harness and planning

- [x] 1.1 Sync `.harness/allowed_files.md` for this remediation branch.
- [x] 1.2 Sync `.harness/review_checklist.md` with high-risk review gates and paused revalidation boundaries.
- [x] 1.3 Validate OpenSpec proposal/design/spec/tasks and run planning self-review.

## 2. RED tests

- [x] 2.1 Add a failing grounded-text payload test proving the prompt lacks an explicit repository-fact extraction contract near hostile evidence.
- [x] 2.2 Add a failing test proving raw hostile evidence remains present while the attack target is not copied into system prompt as a blacklist.
- [x] 2.3 Add a failing test proving same-string legitimate repository identifier behavior remains allowed.
- [x] 2.4 Add a regression test proving `json_object` prompt assembly remains unchanged.

## 3. Implementation

- [x] 3.1 Strengthen grounded-text system prompt and/or user prompt with a compact extraction/data-boundary contract.
- [x] 3.2 Keep evidence snippets intact; do not add output cleaning, marker-specific filtering, evidence suppression, or extra provider calls.
- [x] 3.3 Re-run focused tests and refactor wording only as needed for clarity and deterministic assertions.

## 4. Documentation and verification

- [x] 4.1 Update `docs/PROGRESS.md` and `HANDOFF_TO_NEXT_CHAT.md` only with durable remediation facts.
- [x] 4.2 Run `pytest tests/test_model_provider.py -q` and adjacent focused regression if touched.
- [x] 4.3 Run `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`.
- [x] 4.4 Run `openspec validate harden-grounded-prompt-injection-live-behavior --strict` and `openspec validate --all`.
- [x] 4.5 Run `powershell -ExecutionPolicy Bypass -File scripts/check_stage_docs.ps1` and `git diff --check`.

## 5. Review and closeout

- [x] 5.1 Complete internal review against prompt contract, no-filter boundary, citation behavior, and live revalidation semantics.
- [x] 5.2 Complete independent adversarial external review focused on prompt-injection bypass, false safety, over-constraint, and evidence/citation consistency.
- [x] 5.3 Complete Stage Debt Sweep over changed provider prompt code/tests and direct grounded-answer dependencies.
- [x] 5.4 Resolve all P0/P1/P2 findings and re-run affected verification.
- [x] 5.5 Prepare archive handoff: after archive, merge remediation back into `codex/revalidate-deepseek-provider-conformance` and mark previous revalidation live evidence stale before any renewed live gate.
