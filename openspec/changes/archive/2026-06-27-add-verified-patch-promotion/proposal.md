## Why

RepoPilot can now create retained isolated worktrees, inspect them, re-verify them, and dispose them, but there is still no controlled way to promote a verified worktree patch back into the main workspace. Users currently have a safe isolation lifecycle, not a safe return path.

V25 plans Verified Patch Promotion as the next small stage: only after explicit user confirmation, promote a retained RepoPilot patch worktree that has already succeeded verification, still matches the original controlled patch content, and still matches the original base commit. The planning focus is safety boundaries, state machine, audit, failure semantics, and tests before runtime implementation.

## What Changes

- Add an OpenSpec contract for Verified Patch Promotion without implementing runtime behavior in this planning pass.
- Define promotion eligibility: current `user_id + repo_key` only, existing retained worktree only, worktree lifecycle `verification_succeeded`, related patch status `applied_in_worktree`, main workspace clean, and main `HEAD == base_commit`.
- Require content integrity validation against the stored original controlled patch expectation before any main workspace write; promotion MUST NOT trust current worktree file content directly.
- Require promotion execution to reuse the existing `patch_apply` / `ToolExecutor` / `PermissionPolicy` / `ApprovalGate` boundary rather than copying files from the worktree.
- Define fail-closed behavior: no partial promotion, no automatic retry, no automatic repair, no worktree deletion, no commit/merge/push, and no branch/PR automation.
- Keep public response through existing `/chat.answer`; do not add `/chat` top-level fields or a new public API.
- Synchronize Harness planning boundaries and review gates for a high-risk stage.

## Capabilities

### New Capabilities

- `verified-patch-promotion`: Planned controlled promotion of a verified retained patch worktree into the main workspace after explicit user confirmation and fail-closed preflight.

### Modified Capabilities

- `agent-loop-tool-execution`: Candidate routing and Harness boundary for promotion intent.
- `safe-patch-authoring`: Candidate patch state transition from `applied_in_worktree` to promoted terminal state through scoped stored patch identity.
- `worktree-isolation`: Candidate eligibility and lifecycle interaction for retained worktrees after promotion.
- `persistent-audit-recovery`: Candidate redacted audit event for every recognized promotion attempt.
- `chat-api`: Candidate promotion answers through existing `/chat.answer` only.
- `harness-development-workflow`: High-risk planning and independent plan review gate.

## Impact

- Planning files: `openspec/changes/add-verified-patch-promotion/**`.
- Harness files: `.harness/allowed_files.md`, `.harness/review_checklist.md`.
- Candidate implementation files after explicit confirmation: targeted AgentLoop/parser, ToolExecutor/ToolRegistry/PermissionPolicy context, patch store, worktree manager/preflight, audit manager, and focused tests.
- Durable docs after plan review or implementation: only documents whose owned facts change, likely `README.md`, `docs/ARCHITECTURE.md`, `docs/FEATURE_LIST.json`, `docs/PROGRESS.md`, `HANDOFF_TO_NEXT_CHAT.md`, and relevant long-term specs.
- Dependencies: no network dependency, no provider API key, no default CI or live eval changes.
