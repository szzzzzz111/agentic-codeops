---
name: repo-stage-review-loop
description: Use when a RepoPilot stage plan, implementation, OpenSpec change, or stage documentation needs iterative review before coding, after coding, before archive, or after external feedback.
---

# Repo Stage Review Loop

## Core Rule

Treat a stage as a contract from planning through archive. Run review loops whenever the contract changes: after planning, after external feedback, after implementation, and before archiving.

Final review is a hard gate, not a courtesy pass. If the current OpenSpec change has any unchecked task, stale handoff wording, unresolved review feedback, or missing validation evidence, stop the closeout/archive path and complete final review first.

The human partner owns stage intent and sequencing. Do not turn their confirmation into a code-review burden.

## Mandatory Stop Gates

Before saying "ready to commit", "ready to archive", starting archive, or moving to the next stage, run these checks in order:

1. `openspec list` or `openspec status --change <change> --json` MUST show the active change is complete.
2. `openspec/changes/<change>/tasks.md` MUST have zero `- [ ]` tasks.
3. The last task that says final review, self-review, stage debt sweep, external review, or archive readiness MUST be completed after the final code/doc/test changes, not before them.
4. `HANDOFF_TO_NEXT_CHAT.md`, `docs/PROGRESS.md`, README, ARCHITECTURE, FEATURE_LIST, `.harness/allowed_files.md`, and `.harness/review_checklist.md` MUST agree on whether the stage is planning, implementation, review, complete, archived, or merged.
5. Full verification evidence MUST be current for the present uncommitted workspace, or the missing verification must be recorded explicitly.
6. Long-term `openspec/specs/**/spec.md` MUST NOT contain archive-generated Purpose placeholders such as `TBD`, `TODO`, or `created by archiving change`.
7. Delta spec operation types MUST be archive-syncable: every `MODIFIED` or `REMOVED` requirement header exists in the corresponding long-term spec, and genuinely new requirements use `ADDED`.

If any gate fails, do not archive and do not ask the user to proceed to archive. Fix or record the issue, rerun the relevant validation, then reassess the gates.

Treat ambiguous user phrases like "next step", "continue", "go ahead", or "按流程继续" after implementation as "run final review / stage debt sweep first" unless all stop gates already pass.

## Review Loop

1. Draft or update the OpenSpec change.
2. Run a self-review before implementation.
3. If the user provides OpenCode, Copilot, another model, or human review feedback, triage each finding against repo reality.
4. Fix valid planning/documentation issues one at a time.
5. After implementation, review code, tests, tasks, docs, feature list, and handoff against the OpenSpec contract.
6. Run a Stage Debt Sweep before calling the version complete: scan documentation debt first, then code/test debt; fix in-scope debt or record remaining debt in durable docs.
7. If the user expects OpenCode or another external review pass, stop after internal review and wait for that feedback before saying archive-ready.
8. Before archive, confirm tasks are complete, validation passed, external review has been handled, and long-term specs are ready to receive the delta.
9. Validate the OpenSpec change and report what full verification has or has not run.

Use `external-review-triage` for step 3 when external feedback has P-level findings or concrete file references.

## Self-Review Checklist

Read:

- `openspec/changes/<change>/proposal.md`
- `openspec/changes/<change>/design.md`
- `openspec/changes/<change>/specs/**/*.md`
- `openspec/changes/<change>/tasks.md`
- `.harness/allowed_files.md`
- `.harness/review_checklist.md`
- `README.md`
- `docs/PROGRESS.md`
- `docs/FEATURE_LIST.json`
- `HANDOFF_TO_NEXT_CHAT.md`
- For completed or archived stages, the completed stage's archived `proposal.md`, `tasks.md`, and spec delta.

Check:

- Proposal capability list matches spec delta paths.
- Design decisions match spec requirements and task wording.
- Return structures and API contracts are explicit enough for tests.
- Tasks include tests for every new requirement, non-goal, and security boundary.
- Review checklist includes the latest return structures, exclusions, and gates.
- Feature list reflects planned behavior with `passes: false` until implemented.
- Roadmap order matches the active change.
- README stage history/current snapshot/roadmap, ARCHITECTURE current chain, PROGRESS, FEATURE_LIST, and HANDOFF all agree on the latest completed stage and the current active stage.
- README parity is checked by responsibility area: current snapshot, current capability section, module inventory, stage history, non-goals, and roadmap. A single mention of the completed stage does not satisfy this gate.
- Active change artifacts live under `openspec/changes/<change>/`; long-term specs live under `openspec/specs/<capability>/spec.md`.
- Local `.codex/skills/*` are development helpers, not RepoPilot runtime skills.

## Implementation-Complete Review

After code changes, also check:

- New or changed public functions match the spec return shape and error behavior.
- Tests prove each requirement, non-goal, and safety boundary.
- Tests and docs-check scripts do not lock in stale prior-stage wording, archived markers, capability lists, or roadmap state.
- Tasks are checked only after the corresponding code, tests, docs, or validation actually happened.
- `docs/FEATURE_LIST.json` sets `passes: true` only after deterministic tests pass.
- `docs/PROGRESS.md` and `HANDOFF_TO_NEXT_CHAT.md` report actual validation output, not planned validation.
- README and ARCHITECTURE have been updated for any user-facing capability or runtime-chain change before the stage is treated as done.
- `git status --short --branch` separates stage files from unrelated local helper files.
- A Stage Debt Sweep has been performed:
  - documentation debt across current docs, harness, active OpenSpec, and long-term specs
  - code/test debt across the changed runtime path and adjacent older runtime paths
  - remaining debt recorded in `docs/PROGRESS.md` and `HANDOFF_TO_NEXT_CHAT.md`
- The Stage Debt Sweep evidence is also represented in `.harness/review_checklist.md` and enforced by `scripts/check_stage_docs.ps1` when the debt category is mechanically searchable.

After reporting implementation-complete status:

- Say "ready for external review" if OpenCode or human review has not happened yet.
- Say "ready to commit" only after requested external findings are handled and staged files are clean.
- Say "ready to archive" only after commit sequencing is clear and the user has agreed to archive.

## Archive-Ready Review

Before archive, confirm:

- `openspec list` shows the change as `Complete` and `tasks.md` has no unchecked items.
- `openspec validate <change>` passes.
- For every delta spec, compare operation type and requirement header against its long-term spec. New headers under `MODIFIED Requirements` are an archive blocker even when `openspec validate <change>` passes.
- Full verify ran after implementation changes.
- README, ARCHITECTURE, PROGRESS, FEATURE_LIST, HANDOFF, and long-term specs have been checked against the archived change so the completed stage is not missing from durable docs.
- Long-term specs have real Purpose text; archive-generated placeholders are fixed before archive or recorded as blockers.
- The active change is tracked or committed as intended; no untracked OpenSpec assets remain.
- No unresolved internal, OpenCode, Copilot, model, or human review findings remain.
- The final Stage Debt Sweep has no unrecorded findings.

## Human Confirmation Boundary

Ask the human partner to confirm only stage-level decisions:

- Does the stage goal match what they wanted?
- Are the non-goals acceptable?
- Is the roadmap order acceptable?
- Should the change proceed to external review, commit, merge, push, or archive?

Do not ask the human partner to inspect code, tests, path checks, or line-level implementation details unless they explicitly want to. Those are Codex/reviewer responsibilities.

When summarizing for human confirmation, use 3-5 plain-language bullets. Avoid phrases that imply they must audit code.

## External Feedback Handling

For each finding:

- `fix`: reviewer is correct and the issue is in scope.
- `clarify`: behavior is correct but wording is ambiguous.
- `reject`: suggestion conflicts with the stage scope or repo rules.
- `defer`: concern is valid but belongs to a future stage.

Do not accept feedback blindly. Inspect the referenced files first, then make the smallest scoped change.

## Validation Wording

- Planning-only stages may stop at `openspec validate <change>`.
- Full `scripts/verify.ps1` is required after code or tests change.
- If full verify has not run, say that directly in `docs/PROGRESS.md`, `HANDOFF_TO_NEXT_CHAT.md`, and the final response.
- If validation ran against an uncommitted worktree, say "current uncommitted workspace" or equivalent.

## Communication Rules

- Reply in Chinese by default for this repository unless the user asks otherwise.
- Do not switch final review summaries to English.
- Do not say "ready to archive" immediately after internal self-review if the user has not yet run their expected external review loop.
- Do not describe local `.codex/skills/*` helper edits as RepoPilot runtime behavior.
- Do not stage or commit local helper skills into a feature change unless the user explicitly opens a separate change for them.

## Common Planning Bugs

- Spec says a loader returns content but does not define the return shape.
- Design says a loader reads content but leaves room for parsing or validation creep.
- Tasks omit assertions for return shape, non-goals, or safety boundaries.
- Checklist lags behind spec changes.
- README roadmap and handoff disagree about the current V-stage.
- README stage history omits the just-completed stage while PROGRESS/HANDOFF mention it.
- README mentions the latest stage in the snapshot but omits its current-capability section, module inventory, stage history, non-goal correction, or completed roadmap state.
- A test or docs checker requires a stale prior-stage marker, causing correct documentation updates to fail.
- Post-merge docs claim current HEAD equals the docs commit being created, making the claim stale immediately after commit.
- A delta spec places a new requirement under `MODIFIED Requirements`, so archive sync fails after implementation is already complete.
- ARCHITECTURE current chain still describes the previous stage after a retrieval/runtime chain upgrade.
- Docs imply active change artifacts are already archived.
- Codex asks the human partner to review code details instead of asking for stage-level intent confirmation.
- Codex skips the user's expected OpenCode review step and prematurely declares archive readiness.
- Codex reports validation without saying whether it applied to committed code or the current uncommitted workspace.
- Codex ends a version without scanning and clearing debt from older docs/code touched by the stage.
- Codex only reviews new files and misses adjacent pre-existing runtime paths that the stage depends on.
- Codex leaves remaining debt in chat instead of recording it in `docs/PROGRESS.md` and `HANDOFF_TO_NEXT_CHAT.md`.
- Codex sees `18/19 tasks`, stale "implementation in progress" handoff wording, or an unchecked final review task and still proceeds toward archive.
