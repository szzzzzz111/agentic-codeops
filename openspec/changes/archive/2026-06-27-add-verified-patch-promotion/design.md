## Current Behavior

V20 creates detached locked worktrees for confirmed patch flows. V21 provides scoped read-only inventory and inspection. V22 re-verifies retained worktrees after fail-closed consistency preflight. V23 disposes or reconciles retained worktrees. V24 exposes existing behavior through the local CLI and hardens plan review workflow.

The current runtime still does not promote, commit, merge, push, create branches, create PRs, run background tasks, schedule runtime subagents, use connectors, or modify `/chat` public contract.

## Risk Level

Risk level: `high`.

Reason: promotion would write to the main workspace after consulting retained worktree state, Git metadata, patch storage, verification state, permission/approval context, and persistent audit. This touches patch lifecycle, worktree lifecycle, Git/base consistency, and write-tool safety. The stage should remain high unless repository evidence proves the implementation can be reduced to a narrow wrapper around already-covered `patch_apply` semantics with no new state transitions or Git preflight.

## Target Behavior

Promotion is an explicit confirmed command that takes a scoped worktree id. Candidate command shapes are:

- `confirm promote worktree <worktree_id>`
- `确认提升 worktree <worktree_id>`

The exact command grammar should be finalized during implementation planning review. Missing confirmation, extra text, unsafe ids, user-supplied paths, shell syntax, argv, environment assignments, pipes, redirects, branch names, commit-ish values, or PR/remote hints MUST be rejected as a whole and MUST NOT fall through to repo search, patch apply, verification, or disposal.

## Routing Position

Promotion MUST be a distinct retained-worktree mutation route. Candidate AgentLoop order for V25 is:

```text
memory command
-> long task command
-> assistant control surface
-> worktree inventory / inspection
-> worktree disposal / reconciliation
-> verified patch promotion
-> worktree re-verification
-> patch command / patch intent
-> standalone verification intent
-> audit recovery/status intent
-> capability/status intent
-> repo_search/chat_only fallback
```

Promotion sits after disposal/reconciliation because V23 terminal cleanup and malformed disposal-like requests must remain intercepted first. It sits before re-verification and patch handling so malformed promotion-like requests cannot fall through to verification, patch apply, audit recovery, or repo search.

## Eligibility Preflight

Promotion MUST be scoped to the current `user_id + repo_key`. Unknown, cross-user, and cross-repo worktree ids fail before Git, filesystem, patch, or audit mutation beyond the safe recognized-attempt audit.

Promotion MUST require:

- a retained worktree metadata row in the current scope;
- worktree lifecycle exactly `verification_succeeded`;
- related patch status exactly `applied_in_worktree`;
- main workspace clean, including no tracked changes and no non-ignored untracked files;
- main workspace `HEAD == base_commit`;
- expected worktree path, Git registry/path, lock metadata, common-dir/back-reference, and `HEAD == base_commit` consistent with existing worktree safety rules;
- related stored patch identity and diff hash still matching the original controlled patch record;
- target file content in the retained worktree matching what the stored patch would produce from the stored base content or equivalent controlled patch expectation.

Any missing, stale, inconsistent, malformed, unavailable, or exceptional condition MUST fail closed.

## Content Integrity Rule

Promotion MUST NOT trust the retained worktree's current target files as the source of truth. Worktree content is only evidence to verify that the retained worktree still represents the stored controlled patch result.

The promoted write to the main workspace MUST be derived from the stored original controlled patch and executed through existing `patch_apply` behavior against the main workspace after preflight confirms `HEAD == base_commit` and clean workspace. Direct file copy from the worktree to the main workspace is out of scope and prohibited.

Implementation planning must decide how to compare expected result content. Candidate options:

- replay stored patch preflight in memory against the base/main content and compare resulting target file contents to the retained worktree target files;
- store or reconstruct per-target expected content hashes from the original controlled patch application;
- use the existing patch diff plus base content validation and then independently verify worktree target content against the computed result.

The safest likely direction is replay-and-compare without writing, followed by normal `patch_apply` to the main workspace.

## Harness Boundary

Promotion MUST reuse existing Harness boundaries:

```text
AgentLoop
  -> promotion parser / scoped preflight
  -> ToolRegistry -> PermissionPolicy -> ApprovalGate
  -> ToolExecutor.patch_apply(main workspace, stored patch)
  -> patch/worktree/audit state update
  -> /chat.answer summary
```

If implementation requires a distinct tool name such as `patch_promote`, plan review must justify why `patch_apply` alone cannot express the safe boundary. Even then, no implementation may copy worktree files directly or bypass `PermissionPolicy`, `ApprovalGate`, or `ToolExecutor`.

## Permission Context

Promotion MUST NOT be enabled by loosening the existing ordinary patch confirmation context. Existing direct `patch_apply` confirmation remains valid only for eligible pending patches in its existing flow.

The implementation must define a distinct promotion-safe `ToolInvocationContext`, for example `intent="patch_promotion_apply"` or an equivalent explicit operation kind, carrying only normalized scoped identifiers and the stored patch identity produced by successful promotion preflight. `PermissionPolicy` and `ApprovalGate` must approve this context only after promotion preflight has proven scope, lifecycle, base, content-integrity, and main-workspace cleanliness. A bare `applied_in_worktree` patch id without the promotion preflight context must remain rejected.

## Promotion Atomicity And Partial-Write Boundary

Promotion has a stricter user-facing failure promise than ordinary patch apply: a failed promotion must not leave the main workspace partially promoted. Current `patch_apply` performs full preflight and then writes planned files one by one, restoring already written originals on write failure. That is a good existing boundary, but V25 plan review must decide whether it is strong enough for main-workspace promotion or whether promotion first needs an atomic/staged write enhancement.

Implementation MUST NOT proceed until one of these is chosen and tested:

- reuse existing `patch_apply` only after tests prove the relevant promotion failure modes leave the main workspace unchanged or safely restored;
- extend `patch_apply` with a promotion-safe atomic/staged write path and adjacent regression coverage;
- split the stage so the stored-patch integrity and atomic write foundation lands before enabling promotion.

Any inability to guarantee no partial main-workspace promotion is a blocker, not a documentation caveat.

## State Machine

Candidate successful terminal state:

- patch: `promoted`
- worktree: `promoted`

A distinct `promoted` worktree lifecycle prevents repeated promotion and makes inventory/inspection truthful. The retained worktree MUST NOT be deleted by promotion.

Candidate transition table:

| Current worktree state | Patch state | Promotion request result | Worktree result | Patch result |
|---|---|---|---|---|
| `verification_succeeded` | `applied_in_worktree` | all preflight and write/state steps succeed | `promoted` | `promoted` |
| `verification_succeeded` | `applied_in_worktree` | preflight or approval fails | unchanged | unchanged |
| `verification_succeeded` | `applied_in_worktree` | write fails and no partial main write remains | unchanged or reviewed non-terminal failure state | unchanged |
| `verification_succeeded` | `applied_in_worktree` | write succeeds but state update cannot be made truthful | blocked design case; implementation must journal, roll back, or split before enabling | no untruthful final state allowed | no untruthful final state allowed |
| `promoted` | `promoted` | repeat promotion | rejected safe no-op | `promoted` | `promoted` |
| `verification_failed`, `patch_applied`, `disposal_failed`, `discarded`, unknown | any | any promotion request | rejected | unchanged |

In V25, promoted worktrees are not eligible for re-verification, re-promotion, patch mutation, or V23 disposal. Explicit cleanup/disposal of already promoted retained worktrees would need a future scoped lifecycle change because V23 currently couples disposal to `applied_in_worktree` patch closeout.

Candidate failure states:

- preflight failure: patch and worktree unchanged;
- approval failure: patch and worktree unchanged;
- any failure before main workspace write: patch and worktree unchanged;
- any `patch_apply` failure: main workspace must remain unchanged or be safely restored; patch and worktree remain unchanged unless a safe non-terminal `promotion_failed` state is explicitly added and justified;
- post-apply state update failure: blocker unless the implementation has a durable promotion journal, reversible main-workspace rollback, or another reviewed mechanism that prevents a promoted workspace from being reported as unpromoted;
- audit failure after otherwise successful promotion: audit remains best-effort and must not undo promotion, but the public answer must not claim audit persistence succeeded.

The post-apply state update failure and write atomicity questions are the sharpest state-machine risks and must be resolved in plan review before runtime edits.

## Audit And Public Contract

Every recognized promotion-like attempt MUST attempt to produce one scoped redacted audit event, tentatively `patch_promotion`, related to the worktree id and patch id. Safe fields may include attempt kind, confirmation, preflight classification, execution attempted flag, patch/worktree terminal states, and safe error class.

Audit and public/request-local summaries MUST NOT contain local absolute paths, `.git` paths, DB paths, raw Git output, full diff, patch body, copied file content, environment variables, secrets, raw exception text, or unknown directory names.

Promotion answers MUST use existing `/chat.answer`; `related_files` should remain empty unless the implementation can prove safe repo-relative target file summaries are already public and consistent with existing patch behavior. No `/chat` top-level field may be added.

## Non-Goals

V25 planning and candidate implementation MUST NOT:

- modify `/chat` public contract;
- modify provider runtime, live eval profile, default CI, or require API keys;
- introduce network dependencies;
- implement commit, merge, push automation, branch management, PR creation, background tasks, runtime subagents, connectors, notifications, or always-on behavior;
- execute `git worktree prune`;
- directly copy worktree files over the main workspace;
- trust unverified worktree current content;
- automatically retry, repair, reconcile, delete, or dispose worktrees;
- promote `verification_failed`, `patch_applied`, `disposal_failed`, `discarded`, or unknown lifecycle states;
- treat OpenSpec, Codex/OpenCode skills, Superpowers, MCP, or plugins as RepoPilot runtime capabilities.

## Review Plan

Before any runtime or test implementation, V25 requires:

- internal plan review of proposal, design, tasks, spec deltas, test strategy, and Harness boundaries;
- Codex independent plan review;
- OpenCode independent plan review.

OpenCode review MUST first run `opencode session list`, then reuse a relevant session with `opencode run --session <session_id> ...` when available. If the terminal times out, the session must be inspected for final assistant review text before classifying the review as failed or passed.

All plan findings MUST be triaged as `fix`, `clarify`, `reject`, or `defer`.

## Split Judgment

Default recommendation: keep V25 as one OpenSpec change for planning, because the user-facing capability is one coherent state transition: verified retained worktree to main workspace promotion.

Implementation may need to split if plan review shows two independently risky changes:

- a reusable stored-patch expected-content integrity checker;
- a promotion-safe atomic/staged patch write foundation; and
- the actual main-workspace promotion command/state transition.

Splitting would be justified if the integrity checker or atomic write foundation requires broad patch-store schema or `patch_apply` refactoring that should be reviewed and verified independently before enabling promotion.
