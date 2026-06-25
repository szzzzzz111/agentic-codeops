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
internal plan review, Codex independent plan review, and OpenCode independent
plan review. Plan-level review checks proposal/design/tasks/spec deltas/test
plan/Harness boundaries and roadmap truth. It is separate from final
implementation review.

For OpenCode review, prefer reusing a relevant existing review session:

```powershell
opencode session list
opencode run --session <session_id> "<adversarial plan review brief>"
```

If terminal output times out or does not print the final answer, inspect the
OpenCode session for final assistant review text before declaring the gate
failed. Missing final text is a blocker unless the user explicitly authorizes a
downgrade. Codex subagent review does not replace OpenCode review.

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
