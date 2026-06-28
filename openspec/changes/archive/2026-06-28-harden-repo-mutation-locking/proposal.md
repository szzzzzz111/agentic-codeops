## Why

V25 Verified Patch Promotion closed the main user-facing return path from a verified
retained worktree to the main workspace, but its Stage Debt Sweep recorded one
remaining hardening item: without a repo-scoped mutation lock, a very narrow
cross-process HEAD/file mutation race can still exist between promotion preflight
and write/finalize.

This change plans a small runtime hardening stage: introduce a repo-key scoped
mutation lock for RepoPilot-owned repository mutations. The goal is not a new
product workflow, but a shared safety guard around existing patch/worktree
mutation paths.

## What Changes

- Add an OpenSpec contract for repo mutation locking.
- Require mutation flows that can write repo files, Git worktree metadata, or
  patch/worktree lifecycle state to acquire a lock for the current repo scope
  before their first mutable preflight and to hold it through finalize/rollback.
- Keep read-only routes outside the lock unless they are part of a mutation
  transaction.
- Fail closed before mutation on lock conflict, unavailable lock storage, stale
  owner ambiguity, or implementation uncertainty; if release failure happens
  after a truthful mutation outcome is known, fail closed in reporting and audit
  honesty rather than falsely claiming a clean release.
- Preserve existing `/chat.answer` response behavior and safe audit summaries.
- Avoid any commit, merge, push, branch/PR, background worker, connector,
  notification, retry queue, or `git worktree prune` behavior.

## Capabilities

### New Capabilities

- `repo-mutation-locking`: A repo-key scoped, cross-process lock for RepoPilot-owned
  repository mutation flows.

### Modified Capabilities

- `verified-patch-promotion`: Promotion preflight, write, rollback, and state
  finalization must run under the repo mutation lock.
- `safe-patch-authoring`: Patch apply paths must not bypass the lock when they
  mutate repository files or patch lifecycle state.
- `worktree-isolation`: Worktree creation and patch application into retained
  worktrees must be protected from concurrent RepoPilot mutation flows.
- `worktree-disposal-reconciliation`: Disposal and reconciliation must run under
  the same repo mutation lock before destructive metadata or lifecycle changes.
- `verification-runner`: Whitelisted verification runs are write-risk subprocesses
  and must not race same-repo RepoPilot mutation flows.
- `agent-loop-tool-execution`: Tool execution contexts that perform repository
  mutation must carry lock provenance without changing public response schema.
- `persistent-audit-recovery`: Lock attempts, conflicts, and failures should be
  auditable with redacted scoped summaries.

## Impact

- Planning files: `openspec/changes/harden-repo-mutation-locking/**`.
- Harness files: `.harness/allowed_files.md`, `.harness/review_checklist.md`.
- Candidate implementation files after explicit confirmation: focused lock
  helper/store, mutation call sites in AgentLoop/PatchManager/WorktreeManager/
  VerificationRunner/ToolExecutor, audit summary plumbing, and targeted tests.
- Durable docs after implementation: only documents whose owned facts change,
  likely `docs/ARCHITECTURE.md`, `docs/PROGRESS.md`,
  `docs/FEATURE_LIST.json`, and `HANDOFF_TO_NEXT_CHAT.md`.
- Dependencies: no network dependency, provider API key, default CI change, live
  eval change, new public API, or `/chat` top-level field change.
