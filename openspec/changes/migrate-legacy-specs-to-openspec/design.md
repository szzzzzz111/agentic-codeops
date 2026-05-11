## Context

RepoPilot historically used `specs/00x-*` directories for V1-V4 stage specs. The repository now has project-level OpenSpec support, but `openspec/specs/` is empty, so future agents do not yet have a canonical OpenSpec view of accepted behavior.

This migration is documentation-only. It translates accepted requirements into OpenSpec capabilities while preserving the legacy specs until the migration is reviewed.

## Goals / Non-Goals

**Goals:**

- Create OpenSpec capabilities that cover the accepted V1-V4 behavior.
- Keep the migration reviewable by mapping legacy stage specs into capability-oriented OpenSpec files.
- Preserve existing runtime behavior and tests.
- Keep `.harness` as the source of allowed-files, review checklist, verification, and handoff discipline.

**Non-Goals:**

- Do not modify `app/` runtime code.
- Do not modify `tests/` behavior.
- Do not delete legacy `specs/00x-*` in this planning change.
- Do not introduce MCP, plugin runtime, skill execution, dynamic tool registration, or `/chat` decision changes.

## Decisions

- Use capability-oriented OpenSpec names instead of legacy stage numbers.
  - Rationale: OpenSpec specs should describe long-lived behavior, not just historical implementation phases.
  - Alternative: Mirror `001-*` through `004-*`; rejected because it preserves stage numbering instead of stable capabilities.

- Keep legacy `specs/00x-*` until after OpenSpec migration review.
  - Rationale: The legacy specs are still useful audit history and acceptance context.
  - Alternative: Delete them in the same change; rejected because it makes review harder and risks losing context.

- Represent harness workflow as its own OpenSpec capability.
  - Rationale: RepoPilot's development discipline is part of the controlled Code Agent Harness value, even though it is not runtime code.
  - Alternative: Keep harness rules only in `.harness`; rejected because future OpenSpec changes need a discoverable process contract.

## Risks / Trade-offs

- Legacy specs and OpenSpec specs can temporarily diverge.
  - Mitigation: Keep this as a dedicated migration change, review mappings carefully, and only remove/deprecate legacy specs after acceptance.

- Capability specs may be less chronological than legacy specs.
  - Mitigation: Preserve historical status in `docs/PROGRESS.md` and `HANDOFF_TO_NEXT_CHAT.md`.

- OpenSpec does not replace harness review rules.
  - Mitigation: Keep `.harness/allowed_files.md`, `.harness/review_checklist.md`, verification, and handoff updates mandatory.

## Migration Plan

1. Create OpenSpec capability specs under this change.
2. Review the OpenSpec specs against legacy `specs/00x-*`, README, progress, and feature list.
3. Validate the OpenSpec change.
4. After acceptance, archive the OpenSpec change to populate `openspec/specs/`.
5. In a later cleanup change, decide whether to delete, archive, or keep legacy `specs/00x-*`.

## Open Questions

- Should legacy `specs/00x-*` be deleted after OpenSpec archive, or retained as historical stage documentation?
- Should `docs/FEATURE_LIST.json` remain the acceptability index, or should OpenSpec specs become the primary source and `FEATURE_LIST.json` become derived documentation?
