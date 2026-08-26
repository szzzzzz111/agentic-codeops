---
name: repo-stage-handoff
description: Use when final RepoPilot closeout must prepare durable handoff facts before the reviewed packet and emit one read-only handoff after archived, merged, and pushed state is verified.
---

# Repo Stage Handoff

## Core Rule

Prepare repository-owned durable facts before the final reviewed packet, then
emit one final handoff from live repository facts without another repository
write after the exact candidate commit. Do not turn every archive, merge, push,
or cleanup action into another mandatory documentation cycle.

## Workflow

1. Before freezing the final delivery packet, check live Git/OpenSpec state and
   read `docs/PROGRESS.md`, `HANDOFF_TO_NEXT_CHAT.md`, and only the durable docs
   whose owned facts changed.
2. Update `docs/PROGRESS.md` with durable facts: completed capability or process
   change, important decisions, verification evidence, and unresolved debt.
3. Rewrite `HANDOFF_TO_NEXT_CHAT.md` as short next-session context: baseline,
   blockers, active change if any, and the next safe action.
4. Reset `.harness/allowed_files.md` and `.harness/review_checklist.md` only when
   no active stage remains.
5. Include these final document bytes in the exhaustive reviewed-change
   manifest and final delivery packet. After the packet, permit only the
   schema-valid final implementation `review-set.json` and
   `delivery-binding.json`; after the finite exact candidate commit, do not
   write PROGRESS, HANDOFF, Harness state, or any other repository file.
   Stage replay events/receipts are ordinary pre-tail review subjects, not a
   third evidence-tail channel. Any replay projection after packet freeze
   reopens the packet. Keep the tail exactly the final implementation
   `review-set.json` plus `delivery-binding.json`.
6. After controller-owned merge/push, query live Git state, exact effective
   endpoint, target ref, and OpenSpec state. Emit one report-only final handoff
   and identify anything not verified. Separately report `technical_ready`,
   external `human_authorized`, and `vcs_pushed` (`not_attempted`, `unknown`, or
   `verified`).

## Boundaries

- Query exact branch, commit, and remote state from Git when needed; do not copy
  volatile current-HEAD claims into several documents.
- Do not repeat full stage history in HANDOFF; PROGRESS owns durable history.
- Do not rerun Stage Debt Sweep here unless integration changed behavior or
  exposed new evidence. The reviewed sweep belongs before archive.
- A runtime correction after archive reopens review; it is not handoff cleanup.
- Do not start or imply V-next during closeout.
- Repository authority records and hashes are mechanical-only and cannot assert
  live human authority or push success.
- Repository replay reports/templates are also mechanical-only. Report v2 as
  dormant unless a separate host-capability activation is verified; the
  introducing/in-flight v1 cohort remains v1 through terminal.
- For an activated v2 cohort, query the external terminal tombstone and current
  retained lineage rather than writing them into the repository after push.
- If push outcome is unknown, do not write a reassuring handoff or retry. Report
  `UNKNOWN_PUSH_OUTCOME` and allow only controller-owned, read-only
  reconciliation against the same effective endpoint.

## References

Read `references/stale-state-checklist.md` before finalizing a handoff.
Use `references/evals.md` when changing routing or closeout semantics.
