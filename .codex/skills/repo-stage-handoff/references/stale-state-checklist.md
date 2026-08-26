# Final Handoff Checklist

## Live Facts

Query rather than copy:

```powershell
git status --short --branch
git log -5 --oneline --decorate
git branch --contains HEAD
openspec list
```

Check remote state only when push or remote parity is part of the requested
closeout.

## Document Ownership

- PROGRESS: durable capability/process outcome, decisions, verification, debt.
- HANDOFF: current baseline, active blocker/change, next safe action.
- Review checklist: gate evidence and reviewed paths.
- Git/OpenSpec: exact branch, commit, remote, and active-change state.

Do not copy full stage history into HANDOFF. Do not write exact current-HEAD
claims that become stale when the documentation commit is created.

## Stale-State Search

Look for:

- completed merge/push/archive described as pending
- completed stages listed as future work
- old feature branches described as current
- blockers already resolved
- V-next described as active without an OpenSpec change
- replay/v2 described as active without separate external host capability and
  activation chronology
- an introducing or in-flight v1 stage described as retroactively converted to
  v2, instead of remaining v1 through terminal
- HANDOFF sections that merely repeat PROGRESS history

## Final Gate

- Final runtime/test state was reviewed before archive.
- No runtime/test changes occurred after that review without re-review.
- Blocking findings are closed or clearly stop the next action.
- Relevant deterministic checks passed, or missing checks are explicit.
- Harness files describe no active stage when none exists.
- Durable PROGRESS/HANDOFF/Harness bytes were prepared before the final delivery
  packet and are covered by the reviewed manifest.
- After the final packet, only the schema-valid implementation review set and
  delivery binding were written; after the exact candidate commit, no
  repository file was changed.
- Replay event/receipt projections, if any, were included in the reviewed
  subject before packet freeze and were not added as a third evidence-tail file.
- Any activated-v2 terminal tombstone and retained lineage were queried from
  external host state rather than written after candidate/push.
- The host-retained exact candidate, target branch, effective endpoint, and
  authorized old tip still match the controller preflight.
- `technical_ready`, `human_authorized`, and `vcs_pushed` are reported
  separately; unknown push outcome remains `unknown` pending same-endpoint
  read-only reconciliation.
