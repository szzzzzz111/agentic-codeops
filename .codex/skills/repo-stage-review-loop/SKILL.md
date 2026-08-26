---
name: repo-stage-review-loop
description: Use when a RepoPilot plan or implementation needs formal review, when final code changed after earlier review, or when external findings require evidence-based triage.
---

# Repo Stage Review Loop

## Core Rule

Review the plan contract before implementation when requested, and review the
final implementation state against the approved contract after code changes.
Passing tests and completed tasks are inputs to review, not substitutes for it.

## Plan Contract Review

For plan review, read the proposed plan or active OpenSpec artifacts, Harness
boundaries, relevant specs, and directly implicated runtime/docs. Report
severity-ordered findings against intent, scope, non-goals, test plan,
review gates, and roadmap truth. Medium/high plans require internal plan review
plus two independent plan-review slots before implementation. Each first-round
slot must use a distinct reviewer with no inherited implementation context or
other first-round conclusion; Codex may use an empty-context task or
`fork_turns="none"`. Inherited or unknown context keeps the slot open.

## Review Loop

1. Read the active OpenSpec contract, changed files or plan contract, tests,
   allowed paths, and current review checklist.
2. Confirm the review occurs after the latest runtime/test change.
3. Review in layers: scope, business logic, architecture boundary, minimality,
   failure semantics, security/privacy, test adequacy, and maintainability.
   For user-facing summaries in Chinese, keep precise English terms and add a
   short Chinese explanation or concrete example when the term is non-obvious.
4. Report severity-ordered findings with file/line evidence, trigger,
   consequence, and missing regression coverage. If there are no findings,
   state inspected areas and residual risk.
5. Use `external-review-triage` for external findings. Classify each as `fix`,
   `clarify`, `reject`, or `defer`; never accept it by authority alone.
6. After remediation, rerun affected verification and review changed behavior.
   A same-slot remediation re-review may reuse the original reviewer for finding
   lineage, but every required slot must refresh to the same final content-addressed baseline.
7. Materialize `.harness/reviews/<stage-id>/<phase>/review-set.json` and run
   `python scripts/validate_independent_review.py --project-root . --receipt-set <path> --expected-stage <stage-id> --expected-phase <plan|implementation> --required-slots <count>`.
   Missing receipt evidence, skipped execution, or nonzero exit keeps the gate open.
   A zero exit is mechanical consistency only (`gate_ready=false`); verify
   host-native dispatch provenance and pre-change-authority activation sequence
   separately before counting slots.
8. For final implementation review, consume the canonical byte-stable
   reviewed-change manifest and bounded diff derived from the planning base.
   The review subject excludes exactly four metadata paths: the manifest, diff,
   final review set, and delivery binding. No other path is implicitly excluded.
   Every required slot must bind the same host-retained final packet hash and
   exactly every existing manifest subject plus the manifest and deterministic
   inventory tail; any omission, arbitrary inventory, fifth metadata path, or
   non-tail change after the packet reopens review.
   For replay-capable assets, include all pre-tail event/receipt projections,
   adapter contracts, dormant activation wording, v1 cohort compatibility, and
   v2 template/validator bytes in the normal reviewed subject. A new material
   event or replay write after packet freeze is a non-tail change and reopens
   verification/review/archive; it cannot become a third evidence-tail file.
9. Perform a focused Stage Debt Sweep over changed paths and directly dependent
   older paths. Record inspected paths, concrete findings, dispositions, and
   residual debt.
10. Block archive when tasks are unchecked, review evidence is stale, validation
   failed, blocking findings remain, or delta operations do not match long-term
   specs.

## Review Priorities

- stage scope and user-visible behavior match the approved contract
- business logic, state transitions, and failure paths match intended semantics
- code remains in the correct architectural layer and reuses existing boundaries
- functions/classes stay minimal enough to avoid hidden behavior coupling
- public contract and state-transition correctness
- fail-closed permissions, approval, identity, path, and lifecycle checks
- interruption, retry, rollback, and reconciliation behavior
- tests that assert the intended contract rather than implementation details
- scope drift and accidental roadmap capability claims
- stale assumptions in directly dependent older paths

External review should seek independent counterexamples, especially for
medium/high-risk stages. Repeating the task checklist is not useful diversity.
Reviewer tasks/subagents are development workflow adapters, not RepoPilot runtime
capabilities. Final implementation review uses the risk-contract required-slot
count; the two-slot rule is specific to medium/high plan review.

Review receipts and packet hashes never establish live human authority. Archive
must additionally pass the shared stage-authority `archive` preflight; merge and
push must bind the same final manifest/review set and host-retained exact
candidate under the controller workflow.

Replay reports likewise prove only `mechanical_consistency_only`. Review must
reject any claim that repository bytes activate v2, that an in-flight v1 stage
may change cohort, that replay PASS authorizes/blocks a v1 mutation, or that an
activated-v2 governed action may bypass exact-frontier equality because it is
called unaffected. Real host CAS, restart, dispatch and activation facts remain
external prerequisites.

## Evidence Boundary

Store gate evidence in `.harness/review_checklist.md`. Store durable unresolved
debt in `docs/PROGRESS.md`. Put only next-session blockers in
`HANDOFF_TO_NEXT_CHAT.md`.

Do not perform merge/push handoff here. Return to `repo-stage-workflow`, which
uses `repo-stage-handoff` after integration.

## Evals

Use `references/evals.md` when changing routing or review gates.
