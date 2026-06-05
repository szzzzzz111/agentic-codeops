## Why

V16-V18 made RepoPilot able to propose patches, apply confirmed patches, and run whitelisted verification in a controlled loop. The missing slice is durable, scoped recovery: today a later session cannot ask for a redacted summary of recent trace, patch, verification, or task activity.

V19 adds a lightweight persistent audit layer using repo-local SQLite. It keeps the harness recoverable without introducing external infrastructure, worktrees, real subagents, notifications, or always-on behavior.

## What Changes

- Add a `persistent-audit-recovery` capability with a repo-local `.repopilot/audit.sqlite3` store.
- Persist all `/chat` request trace envelopes as lightweight summaries.
- Persist detailed but redacted summaries for patch attempts, verification results, and long task events.
- Add read-only recovery/status intent through the existing `/chat.answer` surface.
- Keep `/chat` top-level response schema unchanged.
- Make audit writes best-effort: persistence failure MUST NOT fail the primary chat request.
- Strengthen stage workflow gates so Stage Debt Sweep, post-merge durable docs, and branch retention decisions remain checkable.

## Capabilities

### New Capabilities

- `persistent-audit-recovery`

### Modified Capabilities

- `agent-loop-tool-execution`
- `chat-api`
- `safe-patch-authoring`
- `verification-runner`
- `long-task-agent-execution`
- `harness-development-workflow`

## Impact

- Code: `app/audit/**`, `app/harness/kernel.py`, and only minimal adjacent runtime hooks if needed.
- Tests: `tests/test_persistent_audit.py`, targeted AgentLoop and chat API tests.
- Docs: `.harness/allowed_files.md`, `.harness/review_checklist.md`, `README.md`, `docs/ARCHITECTURE.md`, `docs/PROGRESS.md`, `docs/FEATURE_LIST.json`, `HANDOFF_TO_NEXT_CHAT.md`.

## Non-Goals

- No V20 Worktree Isolation.
- No real subagents, connectors, notifications, heartbeat/cron, or always-on assistant.
- No standalone audit API and no new `/chat` top-level fields.
- No replay, rerun, reapply, resume, commit, push, or automatic repair.
- No automatic retention/pruning in V19.
- No workflow/skill/harness discipline as RepoPilot runtime behavior.
