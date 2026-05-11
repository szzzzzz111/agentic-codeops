## Why

RepoPilot now has project-level OpenSpec support, but the accepted V1-V4 requirements still live in the legacy `specs/00x-*` directories. Migrating those requirements into OpenSpec will give future Codex/OpenCode work one canonical spec-driven entrypoint without losing the existing project history.

## What Changes

- Add OpenSpec long-lived specs that capture the accepted V1-V4 capabilities.
- Preserve legacy `specs/00x-*` during the migration review so the old acceptance context remains available.
- After OpenSpec specs are reviewed and accepted, optionally archive or remove legacy `specs/00x-*` in a follow-up step.
- Do not change runtime behavior, APIs, tests, or product capabilities in this migration change.

## Capabilities

### New Capabilities

- `chat-api`: Agent service entrypoint, request/response contract, and trace response shape.
- `safe-repository-file-tools`: Safe read-only repository file tools and path/sensitive-file boundaries.
- `agent-loop-tool-execution`: Minimal deterministic agent loop and unified `ToolExecutor` search boundary.
- `skill-metadata-loader`: DeepAgents-style skill metadata discovery for `.agents/skills/*/SKILL.md`.
- `harness-development-workflow`: Repository development workflow, allowed files, review checklist, verification, handoff, and OpenSpec usage boundaries.

### Modified Capabilities

- None.

## Impact

- Adds OpenSpec specification files under `openspec/specs/`.
- May later archive or remove legacy `specs/00x-*` only after the OpenSpec specs are reviewed.
- No changes to `app/`, `tests/`, API schema, runtime tools, or `/chat` behavior.
