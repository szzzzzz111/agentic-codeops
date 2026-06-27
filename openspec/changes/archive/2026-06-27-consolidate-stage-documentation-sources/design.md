## Risk Level

`medium`.

The stage does not change RepoPilot runtime behavior, public API fields,
persistence, provider wiring, or CI. However, it changes development workflow
contracts, current-stage documentation ownership, and deterministic drift
checks that gate future closeouts. Treating it as medium gives the plan enough
review pressure without overstating runtime risk.

## Current Behavior

Several durable files can describe the same volatile state:

- `README.md` has a current snapshot and roadmap text.
- `docs/ARCHITECTURE.md` sometimes repeats stage sequencing and near-term
  roadmap facts.
- `docs/PROGRESS.md` contains both historical stage entries and current next
  steps.
- `HANDOFF_TO_NEXT_CHAT.md` contains next-session context.
- `docs/FEATURE_LIST.json` includes acceptance notes that can accidentally
  retain old roadmap wording.
- `.harness/allowed_files.md` and `.harness/review_checklist.md` describe the
  current stage boundary.

The V25 closeout exposed the failure mode: a stage can be archived, merged, and
pushed while older current-state wording remains in one of the above documents.
Current scripts catch some stale phrases, but the ownership model is still
loose and makes repeated drift likely.

## Target Behavior

The stage should make documentation ownership explicit and mechanically
checkable where practical:

- Volatile facts such as branch, HEAD, remote sync, and active OpenSpec change
  are read from Git/OpenSpec commands when needed. They are not duplicated as
  durable prose in multiple documents.
- Current capability facts appear only in designated current-state sections.
  Historical stage entries remain append-only history and may contain old
  stage names or backlog wording when historically accurate.
- README stays a concise facade and does not duplicate detailed stage history.
- ARCHITECTURE records stable runtime boundaries and long-lived relationships,
  not transient "currently implementing" tasks.
- PROGRESS owns history, durable decisions, validation evidence, and unresolved
  debt.
- HANDOFF owns only next-session safe action context.
- FEATURE_LIST owns acceptance status and short notes, not roadmap narration.
- Harness files own the active stage boundary and review gate only.
- `scripts/check_stage_docs.ps1` catches stale current-state wording in the
  files and sections that are allowed to describe current facts.

## Non-Goals

- Do not remove important historical evidence from `docs/PROGRESS.md` or
  archived OpenSpec changes.
- Do not make every document generated from one file in this stage.
- Do not introduce a docs build system, templating engine, network dependency,
  or new package dependency.
- Do not change `app/**`, `tests/**`, `/chat`, provider runtime, live eval,
  default CI, or runtime behavior.
- Do not claim OpenSpec, Codex/OpenCode skills, Superpowers, MCP, or plugins as
  RepoPilot runtime capabilities.

## Safety And Boundary Notes

- Because this stage is process/documentation scoped, any runtime, test, or API
  change is out of scope unless a later explicit confirmation widens the
  change.
- Historical archive content should be preserved even when it contains wording
  that is stale today.
- Drift checks should focus on current fact sections and stable stale patterns;
  they should not create fragile false positives against archived history.
- The script should stay Windows-friendly and ASCII-safe where practical, since
  prior PowerShell string encoding issues have already caused parser failures.

## Planned Evidence

- `openspec validate consolidate-stage-documentation-sources --strict`.
- `openspec validate --all`.
- `powershell -ExecutionPolicy Bypass -File scripts/check_stage_docs.ps1`.
- `git diff --check`.
- JSON parse check for `docs/FEATURE_LIST.json` if it changes.
- Focused manual documentation debt sweep covering current-state sections,
  directly changed docs, and adjacent responsibility statements.
- Full `scripts/verify.ps1` if the drift script or long-term workflow spec
  changes.

## Review Plan

Plan review:

- Internal plan review checks proposal/design/tasks/spec delta/Harness boundary
  consistency.
- Codex independent plan review checks for over-broad docs scope, false source
  of truth claims, and review gaps.
- OpenCode independent plan review is required because the stage is classified
  as medium. Reuse an existing review session when possible by running
  `opencode session list` before `opencode run --session <session_id> ...`.
  If the terminal times out, inspect the session for final assistant review
  text before deciding the gate.

All plan findings are classified as `fix`, `clarify`, `reject`, or `defer`.
Implementation waits for explicit user confirmation after plan review.
