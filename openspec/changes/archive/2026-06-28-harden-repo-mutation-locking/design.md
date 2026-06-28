## Current Behavior

RepoPilot now has several controlled mutation paths:

- pending patch apply;
- isolated worktree creation plus patch application;
- retained worktree disposal/reconciliation;
- retained worktree re-verification state updates;
- verified patch promotion into the main workspace.

Each path has scoped preflight, permission/approval boundaries, redacted audit,
and fail-closed behavior. V25 also added atomic/staged patch apply and promotion
rollback semantics. The remaining known risk is a narrow cross-process race:
another RepoPilot process can mutate the same repo scope between a mutation
flow's preflight and its write/finalize step.

## Risk Level

Risk level: `high`.

Reason: even a small lock touches patch lifecycle, worktree lifecycle, Git state,
filesystem writes, persistent stores, and failure semantics. The scope is small,
but the blast radius is the repository mutation boundary.

## Target Behavior

RepoPilot-owned mutation flows MUST acquire a repo-key scoped lock before their
first mutable preflight and hold it until the mutation has either finalized,
failed without writes, or completed rollback/recovery semantics.

The lock is a safety boundary, not a scheduler. It MUST NOT wait indefinitely,
retry in the background, enqueue work, repair state, delete worktrees, or run
commit/merge/push/branch/PR automation.

High-level mutation flows are expected to acquire the repo mutation lock once.
Nested acquisition for the same repo in the same process is not supported in
this stage; if implementation finds a nested mutation call, it must either pass
the existing lock provenance explicitly through the call chain or refuse safely
instead of blocking on itself.

## Lock Scope

The lock key is the normalized existing `repo_key`, not a public path. It is
scoped to the repository identity and shared by all users of the same repo, while
authorization and lifecycle eligibility remain scoped by `user_id + repo_key`.

This intentionally serializes RepoPilot-owned mutations across users for the
same repository because Git HEAD, worktree metadata, and file writes are
repository-global resources.

## Locked Operations

The implementation plan should protect these flows:

- ordinary confirmed `patch_apply` that writes repository files;
- combined patch+verify when its patch step writes;
- V20 worktree creation and patch application into the retained worktree;
- V23 disposal/reconciliation;
- V25 verified patch promotion, including preflight, main-workspace write,
  rollback, and terminal state finalization.
- whitelisted `verification_run` execution when it targets the same repository or
  retained worktree, because the subprocess is a write-risk tool even though its
  argv is fixed.

Read-only inventory, inspection, audit recovery, capability status, memory/task
status, and repo RAG SHOULD remain unlocked. Verification lock handling MUST NOT
add scheduler, queue, retry, background execution, arbitrary shell, or new public
response semantics; it only serializes same-repo write-risk execution while the
command is running and while related lifecycle state is finalized.

## Acquisition Semantics

Recommended first implementation:

- non-blocking acquire;
- deterministic conflict response through `/chat.answer`;
- owner token generated per attempt and stored only in safe internal/audit form;
- release in `finally` after finalize/rollback;
- fail closed if lock storage cannot prove exclusive ownership.

Stale lock handling is a planning risk. This change MUST NOT automatically steal,
reclaim, or override a stale/suspected-stale lock. Any stale, ambiguous, or
suspected owner condition fails closed in this stage; recovery is deferred to a
future explicit maintenance change.

Encountering suspected stale ownership during this change should produce a safe
refusal, a redacted audit summary if available, and a user-facing message that a
repo mutation appears to be in progress or requires a future maintenance
recovery path. It must not expose owner process details, lock storage paths, or
manual deletion instructions.

## Storage Choice

Candidate storage options:

- SQLite lock table in repo-local `.repopilot` state, using an atomic insert or
  compare-and-swap style claim;
- platform file lock under repo-local `.repopilot` state, with Windows-safe
  behavior and tests.

The implementation should choose the smallest option that is cross-process on
Windows, deterministic in tests, and consistent with existing repo-local SQLite
stores. It MUST NOT expose DB paths, local absolute paths, lock files, raw SQLite
errors, or process internals in public responses.

## Harness Boundary

Mutation call sites should pass through a small internal lock guard before
creating or executing write-capable `ToolInvocationContext` values. Tool
execution summaries and audit payloads may include safe fields such as
`lock_acquired`, `lock_conflict`, `operation`, and safe error class, but must not
include local paths, raw exception text, DB paths, Git output, patch body, or file
content.

The lock MUST NOT be represented as a new `/chat` top-level field or public API.

This change uses the centralized `repo-mutation-locking` spec delta to constrain
the existing mutation flows listed in the proposal. During archive, long-term
spec synchronization should either preserve that centralized cross-cutting spec
or add narrow references to impacted capability specs if the final implementation
touches their durable contracts.

## Failure Semantics

- Lock conflict: no mutation, safe refusal, audit best effort.
- Lock storage unavailable: no mutation, safe refusal.
- Preflight failure under lock: no mutation, release lock.
- Write failure under lock: existing flow rollback semantics apply before release.
- State finalization failure: existing promotion/patch/worktree truthfulness
  semantics apply before release.
- Release failure: primary mutation truth remains authoritative, but audit and
  response must not claim clean lock release unless it is known.

No failure path may auto-retry, repair, dispose, prune, commit, merge, push,
branch, PR, or schedule background work.

## Test Strategy

Plan RED tests first for:

- acquire/release/conflict/scope isolation;
- same-process nested acquisition or lock provenance guard behavior;
- non-blocking conflict response;
- lock held from preflight through finalize/rollback for promotion;
- dirty/main HEAD drift checks happening under lock;
- ordinary patch apply not writing without lock;
- whitelisted verification_run refusing safely under same-repo lock conflict;
- worktree create/disposal/reconciliation refusing under conflict;
- failure paths releasing the lock;
- audit redaction and `/chat` contract stability;
- no lock acquisition for read-only inventory/inspection/status/repo search.

Fault injection should cover lock storage failure, conflict, preflight exception,
write failure, rollback/finalize failure, and audit failure.

## Non-Goals

This change MUST NOT:

- change `/chat` public contract;
- modify provider runtime, live eval profile, or default CI;
- introduce network dependencies or provider API key requirements;
- implement commit, merge, push automation, branch management, PR creation,
  background tasks, runtime subagents, connectors, notifications, heartbeat, or
  always-on behavior;
- execute `git worktree prune`;
- directly copy retained worktree files into the main workspace;
- trust unverified worktree current content;
- create a generic distributed scheduler, retry queue, or operator control plane;
- present OpenSpec, Codex/OpenCode skills, Superpowers, MCP, or plugins as
  RepoPilot runtime capabilities.

## Split Judgment

Default recommendation: keep this as one small OpenSpec change because the user
visible behavior is a single hardening boundary: concurrent RepoPilot mutations
of one repo scope are serialized or safely refused.

Split only if implementation evidence shows the lock needs broad store
refactoring, a new recovery protocol, or invasive changes to ToolExecutor/
PatchManager/WorktreeManager that cannot be reviewed safely in one focused
stage.
