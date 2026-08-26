# Stage Planning

## Stage

- Name: `add-stage-change-replay`
- Branch/worktree: `codex/add-stage-change-replay` / isolated worktree
- Risk: `high` / Human Review Depth `L3`
- Risk reason: changes fail-closed repository development action gates and determines which earlier evidence may be retained after material change
- Planning baseline: `bd66dba26f245de6a49999dfde14006d0474ab25`
- Current authority ceiling: `plan`; implementation and all delivery actions await a new exact direct-user envelope
- Proposed stage action ceiling after approval: `push` under the currently active pre-change v1 authority process. This introducing stage remains in the v1 cohort through verified push; v2/replay remains `blocked_on_external_host_capability` and can activate only in a later separately reviewed/approved host-integration stage for newly created stages.
- Proposed VCS target: remote `origin`; fetch/push fingerprint `4cf5d61205314c796fdefe387908a1dc07bf185991d6c08d30314c4bcc6fea1e`; branch `main`; authorized live remote tip `bd66dba26f245de6a49999dfde14006d0474ab25`
- Proposed archive output: `openspec/changes/archive/2026-08-21-add-stage-change-replay/`

## Intent And Scope

- Problem: the active authority gate detects drift but cannot mechanically explain which evidence became stale or the exact earliest gate that must be replayed.
- Outcome: repository-local mechanical validation for controller contexts, append-CAS event/receipt lineages and a conservative V1 suffix graph detects omitted/re-written changes; code-owned evidence adapters model exact-frontier progress; dormant authority/delivery v2 aligns archive-before-candidate without claiming a host adapter or active gate.
- In scope: replay templates, unchanged active v1 authority/delivery producer paths, distinct dormant v2 templates, one replay validator, stage-authority integration, negative tests, Codex/OpenCode workflow/evals, Harness/OpenSpec contracts, review evidence, and closeout.
- Non-goals: RepoPilot runtime change ingestion, durable/background execution, runtime subagents, automatic patch/commit/merge/push, credential handling, hosted identity/approval, public API changes, or importing the Greenfield control plane.
- Public/runtime contract: unchanged; process-only development workflow change.

## Boundaries And Failures

- Owned modules/state: repo-local validators, `.harness/change-replay/**`, dormant workflow interfaces/evals, tests, templates, OpenSpec specs, and stage review/authority artifacts; the real provider-neutral host store is an out-of-scope activation prerequisite.
- Trust boundaries: host-issued workspace identity, initial canonical root, Git common/worktree identities, gate generations, prior/current lineage heads, terminal state, dispatch and direct-user authority are external facts; repository events/receipts only prove mechanical consistency and cannot activate replay.
- Failure behavior: omitted event versus closed snapshot, prefix rewrite, malformed lineage, arbitrary evidence adapter, authority delta mismatch, non-monotonic progress, action behind/ahead of frontier, v1/v2 ambiguity, closed-stage reuse, unsafe ref, or final packet drift fails before mutation.
- Replay rule: V1 uses one code-owned linear suffix/prefix formula and exact fact mapping; no special target skip edges, fixed numeric resume, self-declared later point, or unaffected-action bypass. Planned transition exception requires exact host snapshot pre-state/delta/post-state.
- Audit/privacy: store bounded source references and hashes, never user message bodies, credentials, tokens, or machine-proven identity claims.

## TDD And Verification

- First RED cases: closed input change with `0/none`; prefix rewrite + new head; arbitrary PASS evidence; wrong fact exact sets; action behind/ahead frontier; v1 commit reinterpretation; in-flight v1 owner drift lacking later-v1 producer; caller template/schema cohort switch; plan finding lineage omission; post-packet event; verified-stage reuse; sibling/linked/symlink workspace replay; fake host activation; candidate self-reference.
- Positive cases: mechanical context fixture with exact immutable workspace; empty lineage plus matching open/closed snapshot; single CAS append; in-envelope technical correction; valid per-gate adapters; monotonic exact-frontier progress; dormant v2 implement/archive/commit/merge/push model; pre-candidate delivery binding; unknown-push reconciliation. No fixture is host provenance or activation evidence.
- Focused verification: `pytest -q tests/test_stage_change_replay_validation.py tests/test_stage_authority_validation.py`; workflow structural assertions; changed Python Ruff.
- Full verification trigger: validators/tests change, so run repository verification and record inherited debt separately.

## Review Plan

- Internal review target: event/receipt self-attestation, graph omission, retained-evidence fail-open, authority inheritance, final-packet recursion, and action-gate bypass.
- External review: two independent empty-context plan slots over one frozen packet; same-slot remediation lineage; high-risk two-slot final implementation review.
- Counterexamples requested: omitted event, rewritten prior prefix, arbitrary gate evidence, fact-set mismatch, plan finding misclassification, earlier preserved mutation, action-ceiling deadlock/bypass, v1 introducing/in-flight migration, missing real host capability, sibling/linked worktree replay, candidate-input self-reference, receipt/review recursion, terminal-stage reuse, event after packet, and entrypoint missing context inputs.
- Stage Debt Sweep paths: both validators/tests, independent-review and authority consumers, all changed workflow assets/templates/specs, and final evidence-tail rules.

## Files And Durable Facts

- Allowed files: exact implementation paths and stage-local prefixes are synchronized in `.harness/allowed_files.md`; that list does not itself authorize implementation.
- Review checklist: L3 human gate, two plan and two implementation slots, external authority/change-head claim ceilings, exact graph/set recomputation, and two-file evidence tail.
- Durable docs whose owned facts may change after implementation: `docs/AGENT_RULES.md`, `docs/PROGRESS.md`, final `HANDOFF_TO_NEXT_CHAT.md`, and three long-term specs.
- Facts actually queried/retained by the current controller: branch, HEAD, active change, endpoint/target tip, pre-change authority epoch/hash/schema, packet, candidate, and push state. Replay workspace/snapshot/CAS/terminal fields are only schema/test inputs in this stage and are not claimed as a live durable host capability.

## Human Confirmation

- Plan status: draft pending internal and two-slot independent review.
- Direct-user decision status: the instruction to continue authorizes planning only; it does not carry the previous stage's scope-specific implement/archive/merge/push envelope into this new stage.
- Implementation starts only after: final reviewed plan packet, mechanical plan receipt validation, live target refresh, and explicit direct-user approval of this stage's exact high-risk scope, non-goals, allowed paths, action ceiling, and stop conditions.
- Stop conditions after approval: any scope/path/non-goal/risk/base/action/endpoint/branch/tip drift, stale plan/implementation review, unclosed P0/P1, failed required validation, unknown candidate/merge state, or push ambiguity stops at the affected gate; no automatic rebase/retry/history rewrite.
