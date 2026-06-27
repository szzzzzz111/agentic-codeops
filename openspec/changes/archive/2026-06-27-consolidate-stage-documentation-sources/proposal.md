## Why

RepoPilot stage closeout has repeatedly produced documentation drift: one
current-state document gets updated while another still describes an older
stage as active, future, unmerged, or backlog. The immediate V25 fixes removed
known stale wording, but the root cause is duplicated ownership of the same
volatile facts across README, ARCHITECTURE, PROGRESS, HANDOFF, feature list,
Harness files, and validation scripts.

This stage plans a small process/documentation consolidation: reduce duplicate
"current stage" facts, make each durable document's ownership narrower, and
strengthen deterministic drift checks for mechanically searchable stale facts.
The goal is not to delete useful docs or change RepoPilot runtime behavior; it
is to make future stages harder to close out with contradictory documents.

## What Changes

- Define a single-source policy only for volatile repository state: live Git
  and OpenSpec commands own branch, HEAD, remote sync, and active-change state;
  durable docs should summarize stable facts only where they own them.
- Narrow durable document responsibilities:
  - `README.md`: project facade, current capability snapshot, entry links.
  - `docs/ARCHITECTURE.md`: stable architecture boundaries and durable runtime
    relationships, not transient stage tasks.
  - `docs/PROGRESS.md`: stage history, durable decisions, validation evidence,
    and unresolved debt.
  - `HANDOFF_TO_NEXT_CHAT.md`: next-session action context only.
  - `docs/FEATURE_LIST.json`: acceptance-oriented capability inventory only.
  - `docs/AGENT_RULES.md`: long-term collaboration, branch, review, debt
    sweep, and documentation ownership rules.
  - `.harness/*`: current stage writable and review boundaries only.
  - `scripts/check_stage_docs.ps1`: deterministic stage documentation drift
    checks for mechanically searchable current-fact debt.
- Add or refine deterministic drift checks for current-state sections, while
  preserving archived OpenSpec artifacts and historical PROGRESS entries as
  valid history.
- Plan a focused documentation debt sweep over the current fact paths rather
  than a ritual full-repo scan.
- Keep all public runtime contracts unchanged.

## Capabilities

### New Capabilities

- None. This is a development workflow and documentation governance stage, not
  a RepoPilot runtime capability.

### Modified Capabilities

- `harness-development-workflow`: add requirements for current-fact ownership,
  single-source volatile state, and documentation drift checks.

## Impact

- OpenSpec planning files:
  `openspec/changes/consolidate-stage-documentation-sources/**`.
- Harness files:
  `.harness/allowed_files.md`, `.harness/review_checklist.md`.
- Candidate implementation files after confirmation:
  `README.md`, `docs/ARCHITECTURE.md`, `docs/PROGRESS.md`,
  `docs/AGENT_RULES.md`, `docs/FEATURE_LIST.json`,
  `HANDOFF_TO_NEXT_CHAT.md`, `scripts/check_stage_docs.ps1`,
  `tests/test_chat_api.py` docs-consistency assertions, and
  `openspec/specs/harness-development-workflow/spec.md`.
- Out of scope:
  `app/**`, tests outside the existing docs-consistency assertions, provider
  runtime, live eval profile, default CI, `/chat` public contract, product
  runtime behavior, network dependencies, commit/merge/push automation,
  branch/PR automation, background tasks, runtime subagents, connectors, and
  notifications.
