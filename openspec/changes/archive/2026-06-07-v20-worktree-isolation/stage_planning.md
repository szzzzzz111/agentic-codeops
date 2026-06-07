# Stage Planning

## Stage

- Stage: `V20 Worktree Isolation`
- Proposed branch: `feature/v20-worktree-isolation`
- Capability owner:
  - New capability: `worktree-isolation`
  - Modified capabilities: `agent-loop-tool-execution`, `chat-api`, `safe-patch-authoring`, `patch-verify-loop`, `verification-runner`, `persistent-audit-recovery`, `harness-development-workflow`
- Previous completed stage: `V19 Persistent Audit / Recovery`

## Intent

- Problem:
  - V16-V19 can generate, confirm, apply, verify, and audit patches, but patch apply still mutates the user's main working tree directly.
- Why now:
  - After patch / verify / audit are in place, the next lightweight industrial harness slice is isolating RepoPilot-owned mutations from the user's workspace.
- User-visible outcome:
  - Confirmed patch flows return a retained `worktree_id` and leave the main working tree unchanged.

## Scope

- In scope:
  - Add a repo-local worktree manager, store, and approval-gated `worktree_create` tool.
  - Route standalone patch apply and combined Patch + Verify through an isolated execution repo path.
  - Add read-only `worktree_id` status query via existing `/chat.answer`.
- Out of scope:
  - Worktree list / delete / prune / merge / commit / push.
  - Replaying, rerunning, retrying verification, resuming tasks, or auto-repair.
  - Real subagents, connectors, notifications, heartbeat/cron, always-on assistant.
- API contract:
  - `/chat` top-level fields remain unchanged: `trace_id`, `answer`, `related_files`, `tool_calls`.
- Runtime dependency changes:
  - No external dependency; use Git CLI through fixed argv plus stdlib SQLite.

## Boundaries

- Harness boundaries preserved:
  - Git worktree creation MUST flow through `ToolRegistry`, `PermissionPolicy`, `ApprovalGate`, and `ToolExecutor`.
  - `patch_apply` and combined verification MUST consume an internal `execution_repo_path`, not mutate request routing or public schema.
- Security and audit:
  - Persistent state and public answers MUST NOT expose absolute paths, `.git` internals, full diff, full stdout/stderr, secrets, or DB paths.
- Retrieval stance:
  - grep-first, RAG-assisted remains unchanged; worktree queries are read-only and MUST NOT call repo RAG.

## Tests

- Unit tests:
  - `tests/test_worktree_isolation.py` for Git preconditions, detached/locked creation, lifecycle store, path redaction, and query scope.
- API / contract tests:
  - AgentLoop and `/chat` tests prove worktree-backed patch flows keep existing top-level schema and avoid main workspace mutation.
- Docs / route-map tests:
  - OpenSpec validation, default verify, and stage docs drift checks updated for V20.

## Docs And Harness

- Allowed files to update:
  - OpenSpec change artifacts, worktree runtime/store code, targeted Kernel / ToolExecutor / patch / audit hooks, targeted tests, docs, and harness files.
- Review checklist additions:
  - worktree preconditions, execution path propagation, state transitions, rollback-on-create-failure, query no-create behavior, main workspace unchanged.
- Durable docs to update:
  - `README.md`
  - `docs/ARCHITECTURE.md`
  - `docs/PROGRESS.md`
  - `docs/FEATURE_LIST.json`
  - `HANDOFF_TO_NEXT_CHAT.md`

## Human Decisions

- Decision needed:
  - None. V20 scope, lifecycle, query surface, and failure semantics are locked.
- Default recommendation:
  - N/A
