## Why

`docs/PROGRESS.md` records three small code-debt items around control routing:
capability-status recognition lives as inline string rules in `app/harness/kernel.py`,
some tests still use historical stage names, and the V15 Assistant Control Surface
parser intentionally remains small but needs an explicit non-expansion boundary.

This change resolves those small debts together without adding new user-visible
commands or widening `/chat` behavior.

## What Changes

- Extract capability-status routing checks into a small internal classifier helper
  while preserving the existing route, keyword, reason, and answer text.
- Rename or reshape narrowly targeted historical-stage tests into capability-oriented
  names where that does not weaken the original regression meaning.
- Keep Assistant Control Surface status parsing explicit and narrow; add/keep
  regression coverage that capability-status questions and Long Task / Memory
  commands are not swallowed by status parsing.
- Update OpenSpec, Harness, progress, and handoff only for the real cleanup facts.

Non-goals:

- No new `/chat` top-level fields.
- No new Assistant Control Surface natural-language trigger expansion.
- No answer wording overhaul.
- No provider runtime, live eval, default CI, network dependency, patch/worktree
  behavior, or public API changes.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `agent-loop-tool-execution`
- `assistant-control-surface`

## Impact

- Code: `app/harness/kernel.py`
- Tests: `tests/test_agent_harness_kernel.py`, `tests/test_assistant_control_surface.py`,
  `tests/test_chat_api.py`
- Docs: `docs/PROGRESS.md`, `HANDOFF_TO_NEXT_CHAT.md`
- Harness/OpenSpec: `.harness/allowed_files.md`, `.harness/review_checklist.md`,
  `openspec/changes/cleanup-control-routing-and-test-names/**`,
  `openspec/specs/agent-loop-tool-execution/spec.md`,
  `openspec/specs/assistant-control-surface/spec.md`

Long-term specs are archive-only impact paths; they must not be edited during
implementation except through OpenSpec archive applying the reviewed spec deltas.
