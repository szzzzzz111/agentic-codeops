---
name: repo-stage-workflow
description: Use when running a RepoPilot development stage end to end, from scope and OpenSpec planning through TDD, review, archive, merge, push, and one final handoff.
---

# Repo Stage Workflow

## Core Rule

Run one risk-scaled stage as a controlled sequence. Preserve every required
gate, but create evidence only once and keep each document and skill within its
own responsibility.

## Workflow

1. Read `AGENTS.md` and its required documents. Check branch, worktree, recent
   commits, active OpenSpec changes, and unrelated local edits.
2. Classify the stage as `low`, `medium`, or `high` risk using
   `references/workflow-contract.md`.
3. Use `openspec-stage-planner` to define the stage contract, non-goals,
   writable paths, required evidence, and confirmation boundary. Complete
   plan-level review before implementation: internal plan review, Codex
   independent plan review, and OpenCode independent plan review when required.
4. Use `openspec-apply-change` and `superpowers:test-driven-development` for
   implementation. Do not widen scope to repair unrelated debt.
5. Run focused deterministic verification after each meaningful slice and the
   repository's full verification after runtime or tests change.
6. Use `repo-stage-review-loop` after the final implementation change for final implementation review.
   Review requirements, code, tests, safety boundaries, and changed dependencies.
7. When external review is requested or the risk level requires it, give the
   reviewer an adversarial brief. This applies to plan-level review and final
   implementation review as separate gates. Use `external-review-triage` to
   classify each finding as `fix`, `clarify`, `reject`, or `defer`.
8. Perform a focused Stage Debt Sweep over changed paths and the older paths
   they directly depend on. Record only concrete findings, dispositions, and
   residual risks.
9. Re-run affected verification after every remediation. Archive only when the
   final runtime/test state has passed formal review and all blocking findings
   are resolved.
10. Merge and push only with user authorization. Then use
    `repo-stage-handoff` once to record the stable next-session context.

## Stop Conditions

Stop closeout when scope drift, unchecked OpenSpec tasks, stale review evidence,
unresolved blocking findings, failed verification, archive/spec mismatch, or
unexpected Git state exists.

Do not create V-next planning artifacts during closeout. Do not copy volatile
HEAD hashes into several documents; query Git when exact state is needed.

## Evidence Boundary

- `.harness/review_checklist.md`: operation and gate evidence.
- `docs/PROGRESS.md`: durable capability, decision, validation, and debt facts.
- `HANDOFF_TO_NEXT_CHAT.md`: only what the next session needs to act safely.
- Git/OpenSpec commands: live branch, commit, remote, and active-change state.

## References

Read `references/workflow-contract.md` before selecting gates or reviewers.
Use `references/evals.md` when changing routing, risk levels, or closeout rules.
