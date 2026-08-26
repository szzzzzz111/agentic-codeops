---
name: openspec-stage-planner
description: Use when starting or reshaping a RepoPilot stage, creating an OpenSpec change, choosing risk level, or defining scope before repository implementation.
---

# OpenSpec Stage Planner

## Core Rule

Plan one small stage before implementation. OpenSpec owns the change contract;
Harness owns the writable and review boundary.

## Workflow

1. Read `AGENTS.md`, required project docs, and `openspec/README.md`.
2. Confirm branch, worktree, active changes, and unrelated local modifications.
3. Classify risk as `low`, `medium`, or `high`; state why.
4. Create or update one OpenSpec change with intent, non-goals, exact contracts,
   failure behavior, and acceptance evidence.
5. Update `.harness/allowed_files.md` and `.harness/review_checklist.md` before
   implementation.
6. Name only the durable docs whose owned facts will actually change.
7. Define the internal review target and the required independent slots.
   Medium/high stages require internal plan review plus two independent plan-review slots
   before implementation; reviewer providers are adapters,
   not gate authorities.
8. Complete internal plan review of proposal, design, tasks, spec deltas, test
   plan, and Harness boundaries against each other. Fix contradictions before
   validation.
9. For each first-round independent slot, use a reviewer instance distinct from
   the implementer and other slots, give it the same frozen packet, prevent
   access to other first-round conclusions, and require no inherited context.
   Codex may use a new empty-context task or a subagent with
   `fork_turns="none"`; inherited or unknown context keeps the gate open.
10. Triage every finding before implementation. Same-slot remediation re-review
   may reuse the original reviewer, but every required slot must refresh its
   final receipt against the same final content-addressed baseline.
11. For each required independent plan-review gate, store the actual receipt set
   at `.harness/reviews/<stage-id>/plan/review-set.json` and run the validator
   with the risk-contract count. Medium/high plan review uses `--required-slots 2`;
   a low-risk stage uses its explicit checklist-required slot count, and a
   low-risk stage with no independent-review requirement does not manufacture a
   receipt set. The command is
   `python scripts/validate_independent_review.py --project-root . --receipt-set .harness/reviews/<stage-id>/plan/review-set.json --expected-stage <stage-id> --expected-phase plan --required-slots <count>`.
   Missing receipts, skipped validation, or nonzero exit keeps a
   required gate open. A zero exit proves mechanical consistency only and keeps
   `gate_ready=false`; separately consume host-native dispatch provenance and
   pre-change-authority activation-sequence checks before counting slots.
12. For stages governed by the activated stage-authority gate, define one
   canonical exact/prefix scope envelope and the full host-retained expected
   inputs: stage, epoch, record hash, risk, scope digest, planning base, action
   ceiling, remote name, effective fetch/push endpoint fingerprints, target branch, and
   authorized remote tip. State every invalidation trigger. These expected
   values come from the live host confirmation, not from reading them back from
   the repository record.
13. Record the stage-authority cohort as a host chronology fact. Until an
   independently reviewed activation proves
   `provider_neutral.stage_state_cas/v1`, all stages use pre-change v1 and the
   replay validator is dormant/mechanical-only. The introducing stage and any
   in-flight v1 stage remain v1 through terminal; owner-bound drift uses a later
   v1 authority record. For a newly created, explicitly activated v2 stage,
   plan the immutable workspace binding, host gate snapshot, event/receipt CAS
   heads, exact-frontier action mapping, terminal tombstone, and
   archive-before-candidate ordering. No repository file, template choice, CLI
   boolean, or validator PASS may select the cohort.
14. Validate the change, summarize stage-level decisions in plain language, and
   stop at the implementation confirmation gate.

## Scope Guards

- Do not describe OpenSpec, Superpowers, MCP, plugins, or local skills as
  RepoPilot runtime capabilities.
- Do not claim roadmap capabilities are implemented.
- Do not make every durable document mandatory by default.
- Planning validation proves artifact structure, not design quality.
- OpenCode first-round review uses a new/proven-isolated session. Session reuse
  is limited to same-slot remediation re-review or recovering the same timed-out
  attempt; timeout is not a verdict until final assistant review text is checked.
- A task/subagent used here belongs to the development workflow, not RepoPilot
  runtime. Do not claim runtime subagent support.
- A gate introduced by the current change activates only under the pre-change
  process authority after implementation, negative tests, and workflow wiring.
  The repository validator may bind the activation record hash but cannot prove
  chronology; do not manufacture retroactive plan PASS.
- Repository authority records and hashes are mechanical bindings only. They
  cannot prove user identity, host-message authenticity, chronology, or
  `human_authorized=true`; subagent or reviewer claims cannot elevate them.
- Any later scope, non-goal, risk, planning-base, action-ceiling, endpoint,
  target-branch, or authorized-tip drift invalidates the earlier envelope and
  requires a later epoch plus a new direct-user decision.
- V1 drift keeps the existing later-v1 replacement route. Only a future
  host-activated v2 cohort may add a host-CAS event and replay from the exact
  computed frontier; there is no "unaffected action" bypass.
- Ask the human partner about intent, non-goals, and sequencing, not line-level
  code review.

## References

Read `references/stage-template.md` when drafting a stage or checking scope.
For end-to-end execution, return control to `repo-stage-workflow`.
