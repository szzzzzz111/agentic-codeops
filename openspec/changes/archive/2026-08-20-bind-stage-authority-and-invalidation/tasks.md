## 1. Stage Contract And Plan Review

- [x] 1.1 Create the isolated branch/worktree from live `origin/main` and synchronize the active Harness write/review boundaries.
- [x] 1.2 Create `stage_planning.md`, proposal, design, and both capability deltas with explicit claim ceilings, invalidation triggers, Git target binding, and runtime non-goals.
- [x] 1.3 Run internal plan review and resolve every finding against repository evidence.
- [x] 1.4 Freeze one canonical plan packet and complete two blind empty-context Codex first-round review slots; remediate findings in the same slots and refresh both to one final baseline.
- [x] 1.5 Materialize and validate the actual plan review receipt set, separately verify host dispatch provenance and activation, and run strict/all OpenSpec plus `git diff --check`.
- [x] 1.6 Present the full L3 design, tasks, and spec MUST/SHALL scenarios to the user and obtain renewed explicit confirmation for the corrected archive-path envelope before changing validator/tests/workflow implementation files.
- [x] 1.7 After confirmation, materialize the immutable epoch-1 authority envelope and retain the confirmed epoch/record hash and full expected envelope in host state; do not claim the new gate retroactively authorized planning.

## 2. RED Contract Tests

- [x] 2.1 Add a valid canonical authority-record fixture and assert that mechanical PASS still leaves `human_authorized` external/false and `vcs_pushed` unproven.
- [x] 2.2 Add fail-closed cases for malformed/unknown/sensitive fields, bad hashes, missing host reference, missing expected inputs, record-internal rewrites, stale epoch selection, rollback, gap, sibling/fork-like names, predecessor deletion, and mismatched record lineage.
- [x] 2.3 Add scope-closure cases for allowed-files hash drift and committed/staged/unstaged/untracked/renamed/deleted path escape, canonical path rules, symlinked control artifacts, and submodule/gitlink ambiguity.
- [x] 2.4 Add review/delivery cases for missing or wrong implementation review set, packet hash mismatch, artifact/deletion drift, unrefreshed reviewer slot, byte-stable manifest/diff regeneration, exact four-path metadata exclusion, self-reference avoidance, and any unexpected post-review metadata/path.
- [x] 2.5 Add merge/push cases for empty/evidence-only commit after candidate freeze, wrong explicit source OID, stale/dirty/wrong-branch target worktree, effective endpoint mismatch, pushurl/multiple destination, authorized-tip ancestry failure, exact-lease remote race, and successful same-endpoint postcondition.
- [x] 2.6 Add bounded-process/ambiguous-outcome cases that distinguish pre-mutation timeout/prompt/overflow/kill-reap blockers from any post-push-start timeout/overflow/transport/cleanup ambiguity, which MUST become `UNKNOWN_PUSH_OUTCOME`; also cover server-updated/client-timeout, post-query failure, exact-candidate recovery, unchanged-old-tip safe retry, and third-OID reauthorization.
- [x] 2.7 Add workflow structural assertions that every Codex/OpenCode apply/archive entrypoint consumes the shared gate, subagent/repository claims cannot elevate authority, evidence-tail/handoff ordering is finite, and readiness/authority/push verdicts remain separate.
- [x] 2.8 Run the focused tests and record the expected RED failures before implementation.

## 3. Authority Validator And Workflow Wiring

- [x] 3.1 Add canonical templates for the append-only epoch authority envelope and separate final delivery binding with bounded host reference, exact/prefix scope rules, planning baseline, action ceiling, endpoint fingerprints, target tip, review set, manifest, and evidence tail.
- [x] 3.2 Implement strict schema/hash/action/linear-head validation against the full host-retained expected epoch/record/scope/base/action/endpoint/branch/tip envelope and emit `mechanical_consistency_only` without a repository-derived human verdict.
- [x] 3.3 Implement exhaustive Git change-set/path validation and `.harness/allowed_files.md` hash binding from the exact planning base through committed plus dirty/untracked state.
- [x] 3.4 Integrate the actual independent-review validator, canonical review-subject manifest/diff with an exact four-path metadata exclusion, final packet hash, two-file evidence tail, and exact candidate/source/target preflight for archive/merge/push.
- [x] 3.5 Implement bounded noninteractive Git execution, effective endpoint resolution, same-endpoint `ls-remote`, ancestry check, explicit source/target ref, exact-old-OID lease contract, postcondition verification, redacted failures, and `UNKNOWN_PUSH_OUTCOME` reconciliation semantics.
- [x] 3.6 Update `docs/AGENT_RULES.md`, `.harness/rules.md`, test commands, planning/closeout templates, workflow/planner/review/handoff skills, and every repo-local Codex/OpenCode apply/archive entrypoint/eval to consume the shared gate.
- [x] 3.7 Sync the long-term `stage-authority-binding` and `harness-development-workflow` specs without changing RepoPilot runtime capability docs or `app/**`.
- [x] 3.8 Add and verify the prospective activation record; do not claim the new validator authorized its own pre-implementation plan.

## 4. Verification, Review, And Delivery

- [x] 4.1 Run focused authority/workflow tests, changed-file Ruff, skill/stage structural checks, strict/all OpenSpec validation, full available repository verification, and `git diff --check`; record inherited baseline debt separately.
- [x] 4.2 Freeze the pre-archive implementation manifest/diff and complete the high-risk internal plus independent implementation review required by the risk contract; remediate all blockers before archive.
- [x] 4.3 Perform the focused Stage Debt Sweep over changed paths, the independent-review validator boundary, workflow closeout rules, and live Git target handling.
- [x] 4.4 Activate and validate the current immutable authority envelope for archive, separately verify live host authority, then archive the reviewed change and rerun archive-after validation.
- [ ] 4.5 Prepare final durable docs, nonvolatile handoff/Harness state, activation evidence, and the post-archive delivery manifest/diff; refresh every required reviewer slot to one final packet.
- [ ] 4.6 Write only the schema-valid final implementation review-set JSON and delivery-binding JSON after that packet; validate both, then create the finite exact candidate commit and retain its HEAD in host state.
- [ ] 4.7 Fast-forward integrate only if the reviewed manifest remains exact, then use the confirmed effective endpoint and exact-old-OID lease; reconcile the same remote ref to `verified` or `unknown` without automatic retry/history change.
- [ ] 4.8 After verified push, query live Git/OpenSpec state and emit one final user handoff without another repository write; preserve the unrelated dirty storage-refactor worktree.

Tasks 4.5–4.8 are controller-only delivery protocol. Their live completion is retained by the controller and final
Git/user receipt rather than back-written after final packet or candidate freeze, because any later repository write
would invalidate the reviewed delivery bytes.

Tasks 4.5–4.8 remain controller-owned closeout. This archived task record does not claim that the finite candidate commit, merge, or push has occurred.
