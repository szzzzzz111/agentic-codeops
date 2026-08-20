# RepoPilot Stage Workflow Contract

## Risk Levels

| Level | Typical change | Required review |
| --- | --- | --- |
| `low` | Documentation, local skills, deterministic process checks | Internal review; external review only when requested |
| `medium` | Localized runtime behavior with stable public contracts | Internal review plus focused external review |
| `high` | Git/process execution, subprocesses, persistence, permissions, patch lifecycle, public API contracts | Internal and independent adversarial external review |

Raise the level when uncertainty or blast radius is greater than the file count
suggests. Risk scaling changes review depth, not TDD, verification, or safety
boundaries.

## Responsibility Map

- `openspec-stage-planner`: intent, scope, non-goals, risk, contracts, and
  planned evidence.
- `openspec-apply-change`: task execution against the approved change.
- `superpowers:test-driven-development`: RED-GREEN-REFACTOR discipline.
- `repo-stage-review-loop`: final implementation review and focused debt sweep.
- `external-review-triage`: evidence-based disposition of external findings.
- `openspec-archive-change`: archive mechanics after review readiness.
- `repo-stage-handoff`: one final post-merge/push next-session handoff.

## External Review Contract

Ask an external reviewer to seek independent counterexamples rather than repeat
the task list. Prioritize:

- invalid state transitions and fail-open behavior
- identity, content, lifecycle, permission, and path-boundary mismatches
- rollback, retry, interruption, and reconciliation behavior
- tests that pass while proving the wrong contract
- stale assumptions in directly dependent older paths

Each finding should include severity, location, trigger, consequence, and a
suggested regression test. A reviewer may report no findings, but must state
what was inspected and the residual uncertainty.

## Plan Review Contract

Medium and high risk stages require plan-level review before implementation:
internal plan review plus two independent plan-review slots. Plan-level review
checks proposal/design/tasks/spec deltas/test plan/Harness boundaries and roadmap
truth. It is separate from final implementation review, whose required slot
count remains defined by the risk contract.

Each first-round slot uses a reviewer instance distinct from the implementer and
other slots, reviews the same frozen packet, inherits no implementation context,
and sees no other first-round conclusion. Codex may fill a slot through a new
empty-context task or a subagent invoked with `fork_turns="none"`; inherited or
unknown context is invalid. Provider/model diversity is useful residual-risk
evidence, not a substitute for context and instance isolation.

Same-slot remediation re-review may reuse the original reviewer to preserve
finding lineage. Its receipt must resolve a content-hashed original first-round
receipt with the same slot, reviewer, and finding IDs. It cannot create another
slot, and every required slot must refresh a final receipt against the same
final content-addressed baseline.
OpenCode first-round review uses a new/proven-isolated session; session reuse is
limited to remediation for that slot or recovery of the same timed-out attempt.

Store actual review sets at `.harness/reviews/<stage-id>/<phase>/review-set.json`
and run:

```text
python scripts/validate_independent_review.py \
  --project-root . \
  --receipt-set .harness/reviews/<stage-id>/<phase>/review-set.json \
  --expected-stage <stage-id> \
  --expected-phase <plan|implementation> \
  --required-slots <risk-contract-count>
```

Missing receipts, skipped invocation, or nonzero validation keeps the gate open.
Zero exit proves `mechanical_consistency_only` and keeps `gate_ready=false`:
the host controller must separately verify native dispatch provenance, and the
pre-change process authority must verify activation sequence. A change that
introduces the gate activates it only under that prior authority after
implementation, negative tests, and workflow wiring; the validator may bind an
activation record hash but cannot prove chronology or retroactively validate its
own pre-implementation plan. Empty-context tasks/subagents are development
workflow mechanisms, not RepoPilot runtime capabilities.

## Focused Stage Debt Sweep

Inspect:

1. changed runtime and test paths
2. directly called or state-sharing older paths
3. durable docs whose owned facts changed
4. checks that may encode stale wording or behavior

Do not scan the whole repository by ritual. Expand only when a concrete
dependency or finding justifies it.

## Closeout Invariants

- Formal review evidence postdates the final runtime/test change.
- Archive freezes the reviewed runtime state.
- A runtime correction after archive reopens review and archive readiness.
- `PROGRESS` stores durable facts; `HANDOFF` stores current action context.
- Exact branch, commit, and remote state comes from Git, not duplicated prose.
- Merge/push/cleanup creates one final handoff, not a chain of self-invalidating
  documentation commits.
