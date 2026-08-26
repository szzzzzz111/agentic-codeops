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

## Stage Authority And Delivery Binding

- After activation, apply and archive consume the same fail-closed authority
  validator with host-retained exact expected stage, epoch, record hash, risk,
  scope digest, planning base, action ceiling, remote name, endpoint fingerprints, target
  branch, and authorized old tip. Expected values are not read back from the
  repository record.
- Repository authority evidence is `mechanical_consistency_only`; live human
  authority and host provenance remain external facts.
- The real Git change set includes committed, staged, unstaged, untracked,
  rename, and deletion paths from the planning base. Any exact/prefix scope
  escape or material envelope drift requires a later epoch and direct-user
  decision.
- Final review binds a byte-stable exhaustive manifest/diff. Its subject excludes
  exactly these four metadata paths and no others:
  `.harness/reviews/<stage-id>/implementation/reviewed-change-manifest.json`,
  `.harness/reviews/<stage-id>/implementation/reviewed-change.diff`,
  `.harness/reviews/<stage-id>/implementation/review-set.json`, and
  `.harness/authority/<stage-id>/delivery-binding.json`. The only post-packet
  evidence tail is the latter two schema-valid JSON files. Manifest/inventory
  v2 binds every regular-file subject's content digest and exact
  `100644`/`100755` mode; same-content mode changes after review are drift.
  The four excluded metadata/tail paths use a code-owned canonical candidate
  mode of `100644`; matching worktree/index chmod does not establish review.
- Before creating the finite post-archive candidate, run the shared authority
  validator with `--required-action commit` and the exact final implementation
  review set, slot count, host-retained packet hash, and delivery binding. First
  stage exactly the reviewed subjects plus the four metadata/tail paths and
  require the cached diff check to pass. The validator must bind the staged path
  set, stage-0 regular modes, file/deletion states, and blob bytes to the
  reviewed worktree; the index must not change after preflight. The delivery
  binding, not the pre-archive active-control hash, binds the planned final
  `allowed_files.md` and `review_checklist.md` reset.
- Merge/push are controller-only. They bind the host-retained exact candidate,
  exact merge source/target state, one effective endpoint, authorized old tip,
  ancestry proof, explicit refspec, and exact-old-OID lease.
- A pre-mutation process failure blocks without mutation. Ambiguity after push
  starts is `UNKNOWN_PUSH_OUTCOME`; reconciliation is read-only against the
  same endpoint, and its target branch must equal the separately host-retained
  expected target branch. No automatic retry or history change is allowed.
- POSIX process-group cleanup is valid only for read-only commands. A
  mutation-capable command requires host/cgroup/container/VM whole-tree
  containment or returns `PROCESS_ISOLATION_UNAVAILABLE` before spawn. On
  Windows, start the child suspended, attach it to a kill-on-close Job Object
  before resume, and use cross-platform pipe readers. Mutation intent is
  mandatory, recognizable `git push` cannot be read-only, and pre-resume
  isolation failure is deterministic rather than an unknown push outcome.
- `technical_ready`, `human_authorized`, and `vcs_pushed` are independent
  verdicts. A technical or repository receipt cannot imply another verdict.

## Dormant Stage Change Replay

- The active cohort remains pre-change `stage_authority/v1`. The introducing
  stage and all stages already in flight at later activation remain v1 through
  terminal, including later-v1 authority replacement for authorized drift.
- Repository replay validation proves only `mechanical_consistency_only` and
  neither authorizes nor blocks a v1 mutation. Schema/template selection,
  repository hashes, CLI booleans, fixtures, and dates cannot select v2.
- Blocking v2 requires a separate reviewed activation and external
  `provider_neutral.stage_state_cas/v1` evidence for load, atomic CAS,
  restart-safe recovery, terminal close, immutable workspace binding, and
  host-native reviewer dispatch metadata.
- For a newly created activated-v2 stage, authority core runs before replay.
  Host-retained gate snapshots and event/receipt counts/heads must equal local
  lineage. A governed action must equal the exact current frontier; an earlier
  or later action fails, with no unaffected-action bypass.
- V2 uses `plan -> implement -> archive -> commit(candidate) -> merge -> push`.
  Replay artifacts join the reviewed subject before packet freeze. The final
  evidence tail remains exactly the implementation review set and delivery
  binding; terminal push state is external.
