---
name: repo-stage-handoff
description: Use when a RepoPilot stage has reached its final archived, merged, and pushed state and the next session needs one concise, accurate handoff.
---

# Repo Stage Handoff

## Core Rule

Write one final handoff from live repository facts. Do not turn every archive,
merge, push, or cleanup action into another mandatory documentation cycle.

## Workflow

1. Check live Git state, recent commits, branch containment, remote state, and
   `openspec list`.
2. Read `docs/PROGRESS.md`, `HANDOFF_TO_NEXT_CHAT.md`, and only the durable docs
   whose owned facts changed.
3. Update `docs/PROGRESS.md` with durable facts: completed capability or process
   change, important decisions, verification evidence, and unresolved debt.
4. Rewrite `HANDOFF_TO_NEXT_CHAT.md` as short next-session context: baseline,
   blockers, active change if any, and the next safe action.
5. Reset `.harness/allowed_files.md` and `.harness/review_checklist.md` only when
   no active stage remains.
6. Run relevant deterministic validation and report anything not run.

## Boundaries

- Query exact branch, commit, and remote state from Git when needed; do not copy
  volatile current-HEAD claims into several documents.
- Do not repeat full stage history in HANDOFF; PROGRESS owns durable history.
- Do not rerun Stage Debt Sweep here unless integration changed behavior or
  exposed new evidence. The reviewed sweep belongs before archive.
- A runtime correction after archive reopens review; it is not handoff cleanup.
- Do not start or imply V-next during closeout.

## References

Read `references/stale-state-checklist.md` before finalizing a handoff.
Use `references/evals.md` when changing routing or closeout semantics.
