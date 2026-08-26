## 1. Stage Contract And Plan Review

- [x] 1.1 Create an isolated `codex/add-stage-change-replay` worktree from exact pushed `main` commit `bd66dba26f245de6a49999dfde14006d0474ab25` without touching the unrelated dirty storage-refactor worktree.
- [x] 1.2 Create the proposal, design, capability deltas, stage planning record, and active Harness boundaries with explicit development-only claim ceilings and no fixed `resume_step=1`.
- [x] 1.3 Run an internal consistency/adversarial review over the event schema, V1 gate mapping, replay progress, authority interaction, final evidence tail, and exact path envelope; remove authority/event hash cycles, receipt/review recursion, and impossible downstream pre-closure.
- [x] 1.4 Preserve the two blind first-round receipts for packet `d066a47c…5152`, remediate all A/B findings, freeze one replacement packet, and obtain same-slot re-review from both original reviewers on that exact baseline.
- [x] 1.5 Materialize and validate the plan review receipt set, separately verify host dispatch provenance, and run strict/all OpenSpec plus `git diff --check`.
- [x] 1.6 Present the L3 scope, non-goals, path envelope, v2 action ceiling/order, required evidence, and stop conditions to the user; obtain explicit approval before validator, test, template, workflow, archive, candidate commit, merge, or push mutations.
- [x] 1.7 After approval, materialize the immutable stage authority envelope under the pre-change process and retain its exact expected inputs in controller state; replay context fixtures remain non-authorizing test inputs, not claimed host state.

## 2. RED Change And Replay Contract Tests

- [x] 2.1 Add canonical no-change and changed/ready-for-requested-action fixtures while asserting every PASS remains `mechanical_consistency_only` and does not prove human authority, chronology, semantic correctness, or Git delivery.
- [x] 2.2 Add fail-closed controller-context/CAS lineage cases for omitted or fake external capability, self-attested fallback, omitted event, stale prior/current heads, prefix rewrite plus new head, fork/gap/deletion, concurrent append, host-update-before-validation, restart recovery, sibling clone, linked worktree, symlink/alternate root, unsafe path/schema/control characters, and redaction; fixtures prove only mechanical consistency.
- [x] 2.3 Add event-kind ceiling cases for forged direct-user references, authority/event delta mismatch, technical scope/risk/action/target expansion, plan and implementation remediation without exact same-slot finding lineage, and repository drift that attempts automatic target substitution or history change.
- [x] 2.4 Add parameterized full V1 fact-to-suffix/prefix/frontier exact-set cases, rejecting special target skip edges, receipt omission/extra entries, numeric/later resume, stale graph version, changed dependency with byte-stable consumer, and unsafe refs.
- [x] 2.5 Add per-gate adapter forgery cases for arbitrary PASS files, unknown producer/schema, wrong argv/cwd/subject/generation, partial verification command set, mechanical review PASS without host dispatch, recursive authority/replay input, stale tail/live facts, and valid adapter progress.
- [x] 2.6 Add full frontier × governed-action tests: exact frontier positive; earlier preserved action `ACTION_BEHIND_REPLAY_FRONTIER`; later action blocked; no-change normal-sequence snapshot checks; event required before returning to implementation; all failures pre-mutation.
- [x] 2.7 Add v1/v2 action-ceiling/cohort tests for the introducing stage, in-flight v1 stages at multiple frontiers, terminal v1 stages, and future new v2 stages; cover owner-authorized scope/risk/endpoint/tip drift with later-v1 replacement, rejection of v2 downgrade/template selection, archive-before-candidate, authority trigger event, exact pre-candidate delivery inputs/no candidate OID, immutable post-candidate binding, terminal/restart/unknown-push cases.
- [x] 2.8 Add structural tests for every supported Codex/OpenCode apply/archive entrypoint: pre-change remains active, dormant replay cannot authorize/block mutation, fake activation is rejected, and assets never become `app/**`; record the real host adapter positive/restart/CAS tests as an unmet later-activation prerequisite, then run and preserve RED evidence.

## 3. Replay Validator And Authority Integration

- [x] 3.1 Keep the existing authority/delivery template paths byte-compatible active v1 producers; add distinct dormant `stage-authority-record-v2` and `stage-delivery-binding-v2` templates plus strict change-event/replay-receipt templates with canonical CAS lineage, immutable workspace binding, trigger-event, replay-head, graph, adapter, gate-set, exact pre-candidate construction inputs, and claim-ceiling fields.
- [x] 3.2 Implement `scripts/validate_stage_change_replay.py` with exact canonical root, strict schema/path safety, host gate snapshots, prior-prefix append CAS, current-head action equality, structured redacted failures, and bounded recovery reports.
- [x] 3.3 Implement the code-owned V1 linear graph and complete fact-to-suffix/prefix mapping with no special edges; recompute all sets and exact frontier.
- [x] 3.4 Implement the per-gate evidence adapter matrix, monotonic progress, snapshot generations, tail/live composition, and outer-authority-core-first separation without receipt recursion.
- [x] 3.5 Extend `validate_stage_authority.py` with a dormant v2 archive-before-commit model while preserving the active v1 producer/template and later-v1 replacement path through terminal; bind v2 authority trigger event, delivery replay heads, and exact non-self-referential pre-candidate inputs.
- [x] 3.6 Expose replay validation as a non-authorizing mechanical interface: it recomputes exact-frontier readiness, but active v1 implement/archive/commit/merge/push behavior remains unchanged and a request to activate without the external capability fails `HOST_STATE_UNAVAILABLE` before mutation.
- [x] 3.7 Keep workspace issuance, host CAS state, reviewer dispatch, direct-user authority, terminal tombstone, activation chronology, and push success external; repository outputs remain `mechanical_consistency_only`, with activation status fixed to `blocked_on_external_host_capability`.

## 4. Workflow, Harness, And Durable Contract Sync

- [x] 4.1 Update RepoPilot Codex planning/apply/archive/review/workflow/handoff and relevant evals to expose the dormant mechanical contract, preserve plan/implementation finding lineage, reject fake activation, and keep the pre-change gate authoritative until a later host-capability stage.
- [x] 4.2 Update the corresponding OpenCode plan/apply/archive commands and skills with the same dormant/unsupported activation boundary; do not claim OpenCode has a durable host adapter.
- [x] 4.3 Update Harness rules, test commands, authority/delivery/replay/planning/closeout templates, allowed paths, and review checklist without adding a third final evidence-tail file.
- [x] 4.4 Sync long-term `stage-change-replay`, `stage-authority-binding`, and `harness-development-workflow` specs plus the currently changed `docs/AGENT_RULES.md`; defer archive-state `docs/PROGRESS.md` and final `HANDOFF_TO_NEXT_CHAT.md` updates to task 5.4 so they do not preclaim closeout.
- [x] 4.5 Verify `app/**`, public `/chat`, runtime capability reporting, persistence/provider behavior, dependencies, and network defaults remain unchanged.

## 5. Verification, Review, Archive, And Delivery

- [x] 5.1 Run focused replay/authority/workflow tests, changed-file Ruff, skill/stage structural checks, strict/all OpenSpec validation, full available repository verification, and `git diff --check`; separate inherited baseline debt.
- [x] 5.2 Freeze the exhaustive pre-archive implementation packet and complete high-risk internal plus two-slot independent implementation review; remediate all blockers in the same slots and perform the focused Stage Debt Sweep.
- [x] 5.3 Record replay as `blocked_on_external_host_capability`, validate archive authority under the unchanged pre-change v1 process, archive the reviewed change to `openspec/changes/archive/2026-08-21-add-stage-change-replay/`, and rerun post-archive validation without activating v2.
- [ ] 5.4 Prepare final durable docs and the post-archive delivery packet; refresh every required reviewer slot to one exact final baseline.
- [ ] 5.5 Write only the schema-valid final implementation `review-set.json` and `delivery-binding.json` as the evidence tail, validate them, create one finite exact candidate commit, and retain its HEAD in host state.
- [ ] 5.6 Fast-forward integrate only if the reviewed manifest remains exact, then push only with the confirmed endpoint, branch, candidate, authorized old tip, and exact-old-OID lease; reconcile the same remote ref to `verified` or `unknown` without automatic retry/history change.
- [ ] 5.7 After verified push, query live Git/OpenSpec state and emit one concise final handoff without another repository write; report replay/v2 still inactive and name the later host-capability activation prerequisite; preserve the unrelated dirty storage-refactor worktree.

Tasks 5.4–5.7 are controller-owned closeout. Their live completion is retained by the controller and final Git/user receipt rather than back-written after final packet or candidate freeze, because any later repository write would invalidate the reviewed delivery bytes.
