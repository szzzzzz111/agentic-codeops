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
review gates, and roadmap truth. Medium/high plans should receive internal,
Codex independent, and OpenCode independent review before implementation.

## Review Loop

1. Read the active OpenSpec contract, changed files or plan contract, tests,
   allowed paths, and current review checklist.
2. Confirm the review occurs after the latest runtime/test change.
3. Report severity-ordered findings with file/line evidence, trigger,
   consequence, and missing regression coverage. If there are no findings,
   state inspected areas and residual risk.
4. Use `external-review-triage` for external findings. Classify each as `fix`,
   `clarify`, `reject`, or `defer`; never accept it by authority alone.
5. After remediation, rerun affected verification and review changed behavior.
6. Perform a focused Stage Debt Sweep over changed paths and directly dependent
   older paths. Record inspected paths, concrete findings, dispositions, and
   residual debt.
7. Block archive when tasks are unchecked, review evidence is stale, validation
   failed, blocking findings remain, or delta operations do not match long-term
   specs.

## Review Priorities

- public contract and state-transition correctness
- fail-closed permissions, approval, identity, path, and lifecycle checks
- interruption, retry, rollback, and reconciliation behavior
- tests that assert the intended contract rather than implementation details
- scope drift and accidental roadmap capability claims
- stale assumptions in directly dependent older paths

External review should seek independent counterexamples, especially for
medium/high-risk stages. Repeating the task checklist is not useful diversity.

## Evidence Boundary

Store gate evidence in `.harness/review_checklist.md`. Store durable unresolved
debt in `docs/PROGRESS.md`. Put only next-session blockers in
`HANDOFF_TO_NEXT_CHAT.md`.

Do not perform merge/push handoff here. Return to `repo-stage-workflow`, which
uses `repo-stage-handoff` after integration.

## Evals

Use `references/evals.md` when changing routing or review gates.
