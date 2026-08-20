## 1. Stage Contract And Plan Review

- [x] 1.1 Create the isolated branch/worktree and synchronize `.harness/allowed_files.md` and `.harness/review_checklist.md` before workflow/spec/test implementation.
- [x] 1.2 Create proposal, design, and `harness-development-workflow` delta artifacts that preserve two independent review slots and keep runtime subagents out of scope.
- [x] 1.3 Run internal plan review and strict OpenSpec validation; resolve artifact contradictions.
- [x] 1.4 Complete the pre-change-contract empty-context Codex plan review, same-slot remediation re-reviews, final packet hashes, and dispositions in `plan-review.md` without claiming retroactive validator PASS.

## 2. Structural Tests

- [x] 2.1 Replace the provider-hardcoded workflow skill assertions in `tests/test_cli.py` with RED assertions for two plan-review slots, empty-context Codex substitution, inherited-context rejection, final-baseline refresh, re-review continuity, and process-only/runtime separation.
- [x] 2.2 Add RED validator tests for implementer/reviewer identity collision, duplicate reviewers, inherited/unknown context, cross-review visibility, mutable/mismatched baseline, stale remediation receipts, missing actual receipt sets/nonzero validation, valid first/re-review sets, and the self-bootstrap rule that a newly introduced gate activates only after its implementation/verification.
- [x] 2.3 Run the focused workflow/validator tests and record the expected failure before editing workflow rules, skills, adapter, or validator implementation.

## 3. Workflow Contract Implementation

- [x] 3.1 Update `docs/AGENT_RULES.md` and `.harness/rules.md` to require provider-neutral independent review slots and evidence.
- [x] 3.2 Update `openspec-stage-planner`, `repo-stage-workflow`, `repo-stage-review-loop`, `workflow-contract`, and both workflow/review-loop eval references so first-round Codex substitution uses an empty-context task or parent-context-disabled subagent while remediation re-review may reuse the original reviewer session.
- [x] 3.3 Update the OpenCode plan-review adapter so first-round review uses an isolated session and session reuse is limited to the same slot's remediation/timeout recovery.
- [x] 3.4 Add the fixed independent-review receipt template and deterministic validator.
- [x] 3.5 Wire the exact receipt-set validator command into workflow/planner/review-loop/rules so missing receipts, skipped invocation, or nonzero exit keeps the independent-review gate open; record that activation begins after this change implements and verifies the gate, not retroactively for its plan review.
- [x] 3.6 Update the long-term `harness-development-workflow` spec to match the reviewed delta without changing runtime capabilities.
- [x] 3.7 Confirm historical archive/progress review facts are unchanged.

## 4. Verification And Closeout

- [x] 4.1 Run focused workflow structural tests, stage-doc/skill-eval scans when available, strict change validation, and `openspec validate --all`.
- [x] 4.2 Activate the new validator after implementation/negative tests, then materialize and validate this stage's actual final receipt set; do not create a retroactive plan-validation claim.
- [x] 4.3 Run full repository verification when available plus `git diff --check`; record exact environmental limits instead of claiming unrun gates passed.
- [x] 4.4 For this user-requested low-risk stage, run one empty-context Codex independent final review against the frozen final diff and triage/repair all blocking findings; do not encode this as a universal two-slot final-review count.
- [x] 4.5 Perform a focused Stage Debt Sweep and update `.harness/review_checklist.md`, `docs/PROGRESS.md`, and `HANDOFF_TO_NEXT_CHAT.md` with owned final facts only.
- [x] 4.6 Confirm the original dirty storage-refactor worktree is unchanged and stop without merge or push.
