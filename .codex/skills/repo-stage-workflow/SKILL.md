---
name: repo-stage-workflow
description: Use when running a RepoPilot development stage end to end, from scope and OpenSpec planning through TDD, review, archive, merge, push, and one final handoff.
---

# Repo Stage Workflow

## Core Rule

Run one risk-scaled stage as a controlled sequence. Preserve every required
gate, but create evidence only once and keep each document and skill within its
own responsibility. OpenSpec owns the specification baseline; execution
discipline skills own how the approved baseline is implemented and verified.

## Operating Split

- OpenSpec owns requirement clarification, interface/model/design decisions,
  task decomposition, spec review, requirement changes, and archive.
- Superpowers-style execution discipline owns reading the approved baseline,
  worktree/branch isolation when needed, TDD, deterministic verification, code
  review, finishing, and skill/process self-checks.
- If implementation reveals requirement drift, design contradiction, or scope
  change, return to OpenSpec planning/exploration before implementation
  resumes. Regenerate or update the execution plan from the new baseline.
- Treat OpenSpec, Superpowers, local skills, MCP, plugins, and connectors as
  development workflow references only. Do not describe them as RepoPilot
  runtime capabilities unless a future runtime OpenSpec change explicitly says
  so.

## Workflow

1. Read `AGENTS.md` and its required documents. Check branch, worktree, recent
   commits, active OpenSpec changes, and unrelated local edits.
2. Classify the stage as `low`, `medium`, or `high` risk using
   `references/workflow-contract.md`.
3. For fuzzy or high-expansion themes such as MCP, Skill, subagent, connector,
   runtime plugin, background worker, durable execution, or always-on assistant,
   run a lightweight Grilling Gate before writing OpenSpec artifacts. Pin down
   terminology, counterexamples, runtime availability, approval/audit boundary,
   and non-goals. Skip this gate for ordinary narrow bugfix, documentation, or
   known-debt stages unless the user asks.
4. Use `openspec-stage-planner` to define the stage contract, non-goals,
   writable paths, required evidence, and confirmation boundary. Complete
   plan-level review before implementation: internal plan review plus two
   independent plan-review slots for medium/high stages. Provider choice does
   not change the slot count. A Codex reviewer must use a new empty-context task
   or `fork_turns="none"`; inherited/unknown context cannot satisfy a slot.
   First-round slots review the same frozen packet without seeing each other's
   conclusions. A same-slot remediation re-review may reuse its original
   reviewer, but all required slots must refresh to the same final
   content-addressed baseline.
   For ordinary narrow stages, the agent reads the full proposal/design/tasks/spec
   and gives the user a concise Chinese summary plus one implementation
   confirmation gate. Calibrate the human plan-review depth using the
   "Human Review Depth" section below; do not require the user to review every
   artifact line by default.
5. After prospective activation of the shared stage-authority gate, retain the
   live host-confirmed exact stage, epoch, authority-record hash, risk, scope
   digest, planning base, action ceiling, remote name, effective fetch/push endpoint
   fingerprints, target branch, and authorized remote tip. Run the shared
   validator with `--required-action implement` and the exact flags documented
   in `.harness/test_commands.md` before implementation mutation.
   Do not reconstruct expected values from the record being validated. A
   missing/stale record, scope/path drift, invalid lineage, insufficient
   ceiling, or expected-input mismatch fails closed. Validator success proves
   mechanical consistency only; live direct-user authority remains a separate
   host check. A change introducing this gate stays under the pre-change process
   until prospective activation and cannot self-authorize retroactively.
6. Use `openspec-apply-change` plus the relevant Superpowers execution skills
   for implementation discipline: read the approved baseline, isolate work when
   needed, write RED tests first for behavior changes, keep changes minimal, and
   do not widen scope to repair unrelated debt.
7. Run focused deterministic verification after each meaningful slice and the
   repository's full verification after runtime or tests change.
8. Use `repo-stage-review-loop` after the final implementation change for final implementation review.
   Review requirements, code, tests, safety boundaries, and changed dependencies.
   Prepare a concise human review packet before archive/merge review when the
   stage is L2 or L3, or when the user asks for one.
9. When external review is requested or the risk level requires it, give the
   reviewer an adversarial brief. This applies to plan-level review and final
   implementation review as separate gates. Final implementation review keeps
   the risk-contract slot count; it does not inherit the medium/high plan count
   automatically. Use `external-review-triage` to classify each finding as
   `fix`, `clarify`, `reject`, or `defer`.
10. For every required independent-review gate, materialize the actual receipt
   set under `.harness/reviews/<stage-id>/<phase>/review-set.json` and consume:
   `python scripts/validate_independent_review.py --project-root . --receipt-set <path> --expected-stage <stage-id> --expected-phase <plan|implementation> --required-slots <count>`.
   Missing receipts, skipped invocation, or nonzero exit leaves the gate open.
   Zero exit is `mechanical_consistency_only`, not `gate_ready`: also verify
   host-native dispatch provenance and the pre-change authority's activation
   sequence. Repository-authored labels cannot prove either external fact.
11. Perform a focused Stage Debt Sweep over changed paths and the older paths
   they directly depend on. Record only concrete findings, dispositions, and
   residual risks.
12. Re-run affected verification after every remediation. Before archive,
   generate the byte-stable exhaustive reviewed-change manifest and bounded
   diff. The review subject excludes exactly the canonical manifest, diff,
   final review-set, and delivery-binding paths; no fifth metadata path is
   allowed. Archive only when the actual implementation review set is valid for
   that subject and all blocking findings are resolved.
13. Run the shared validator with `--required-action archive`, the exact flags
   documented in `.harness/test_commands.md`, and the actual
   implementation review set, required slot count, and host-retained packet
   hash before archive mutation. After archive and final durable docs are
   prepared, refresh every required reviewer slot to one final packet. Only the
   schema-valid final `review-set.json` and `delivery-binding.json` may be added
   afterward; any other write reopens review.
14. Create the finite candidate commit and retain its exact HEAD externally.
   Merge and push remain controller-only actions: validate exact feature HEAD
   and merge source, clean exact target branch/pre-merge OID, final manifest,
   delivery binding, shared Git common-directory identity, live endpoint
   fingerprints, branch, and authorized old tip. Pass `--explicit-source-oid`,
   `--merge-target-worktree`, and `--expected-target-premerge-head` for merge.
   Merge only with `git merge --ff-only <exact-candidate-oid>` and verify the
   target equals that OID.
15. Push only after the exact effective endpoint reports the authorized old tip
   and ancestry proves it is an ancestor of the candidate. Use an explicit
   source OID, target ref, and exact-old-OID lease. Once push starts, timeout,
   output overflow, transport ambiguity, or cleanup ambiguity becomes
   `UNKNOWN_PUSH_OUTCOME`; do not claim no mutation and perform only read-only
   same-endpoint reconciliation before any retry. Reconciliation must compare
   the caller target branch with the separately host-retained expected target
   branch before querying. A POSIX process group is read-only containment only;
   do not spawn a mutation-capable command unless the host, a cgroup, container,
   or VM supplies an inescapable whole-tree boundary. The repository runner
   returns `PROCESS_ISOLATION_UNAVAILABLE` before spawn otherwise. On Windows,
   bind a suspended child to a kill-on-close Job Object before resume and drain
   pipes without selector-only assumptions. Pass mutation intent explicitly;
   never label a recognizable `git push` read-only, and classify failure before
   successful Windows resume as deterministic isolation failure. Never
   auto-fetch/rebase, choose another target, rewrite history, or
   non-fast-forward push.
16. Use `repo-stage-handoff` once. Prepare repository docs before the final
   packet/candidate; after merge/push, query live state and emit the final
   handoff without another repository write. Report `technical_ready`,
   `human_authorized`, and `vcs_pushed` separately, with push state at least
   `not_attempted`, `unknown`, or `verified`.

## Human Review Depth

Choose the human review depth by risk trigger, not by line count alone. Small
diffs can still be high-risk when they touch public contracts, mutation,
approval, audit, sandbox, persistence, provider runtime, network behavior, or
new runtime capability boundaries.

### L1: Small / Low-Risk

Use L1 for wording, test naming, internal helpers, local cleanup, or docs that
do not change public contracts, mutation paths, routing semantics, permission,
approval, audit, persistence, provider runtime, or user-visible runtime
behavior.

Before implementation, give the user a concise summary, decision points,
non-goals, and planned test coverage. Do not ask for line-by-line review of
`proposal.md`, `design.md`, `tasks.md`, or spec deltas unless the user asks or
scope is unclear.

After implementation, point the user to the changed diff and the tests that
prove the original boundary still holds.

### L2: Medium / User-Visible Or Routing-Sensitive

Use L2 when the stage changes user-visible behavior, status wording, routing,
`ToolRegistry`/tool metadata interpretation, Assistant Control Surface wording,
or other control-plane behavior, while avoiding new permission, persistence,
public API field, provider runtime, network, or mutation-policy changes.

Before implementation, summarize the stage and ask the user to review the
decision-level parts only: `design.md` Goals/Non-Goals, Decisions,
Alternatives, Risks/Trade-offs, and `tasks.md` test coverage. The agent still
owns low-level implementation choices.

After implementation, provide a human review packet with changed file map,
behavior changes, focused and full verification evidence, residual risks, and
the key code paths the user should inspect.

### L3: Large / High-Risk

Use L3 for new runtime APIs, persistence or audit models, permission/approval
or sandbox changes, provider runtime changes, network dependencies, dynamic
tool registration, real MCP/Skill/connector/subagent execution, durable
execution loops, or any stage where failure behavior materially changes user
risk.

Before implementation, ask the user to review full `design.md`, full
`tasks.md`, and the spec delta MUST/SHALL scenarios. When useful, run an
adversarial review focused on counterexamples, non-goals, permission boundary,
failure behavior, and missing tests before implementation starts.

After implementation, provide the human review packet, final review findings,
test and verification evidence, and the archive/merge risk summary. Do not
archive or merge while blocking human-review questions remain open.

## Stop Conditions

Stop closeout when scope drift, unchecked OpenSpec tasks, stale review evidence,
unresolved blocking findings, failed verification, archive/spec mismatch, or
unexpected Git state exists.

Also stop on a missing/stale authority epoch, host-expected envelope mismatch,
unreviewed subject drift, candidate HEAD drift, effective endpoint ambiguity,
authorized-tip mismatch, non-fast-forward ancestry, or unknown push outcome.
An unknown push outcome permits same-endpoint read-only reconciliation only.

Do not create V-next planning artifacts during closeout. Do not copy volatile
HEAD hashes into several documents; query Git when exact state is needed.

## Evidence Boundary

- Empty-context tasks and subagents in this skill are development workflow
  reviewer adapters, not RepoPilot runtime capabilities.
- `.harness/review_checklist.md`: operation and gate evidence.
- `docs/PROGRESS.md`: durable capability, decision, validation, and debt facts.
- `HANDOFF_TO_NEXT_CHAT.md`: only what the next session needs to act safely.
- Git/OpenSpec commands: live branch, commit, remote, and active-change state.

## References

Read `references/workflow-contract.md` before selecting gates or reviewers.
Use `references/evals.md` when changing routing, risk levels, or closeout rules.
