# worktree-isolation Specification

## Purpose

定义 RepoPilot 的 V20 Worktree Isolation 边界：系统通过 repo-local 受控 Git worktree 隔离 RepoPilot 产生的 patch apply 与组合 Patch + Verify 执行，使主工作区保持不变，并通过现有 `/chat.answer` 提供只读 worktree 状态查询。
## Requirements
### Requirement: Worktree Creation Is Approval-Gated

系统 SHALL provide a `worktree_create` tool that is registered as `read_only=False`, `risk="write"`, and `requires_approval=True`. Worktree creation MUST pass through `ToolRegistry`, `PermissionPolicy`, `ApprovalGate`, and `ToolExecutor`.

Worktree creation MUST use fixed Git argv with `shell=False`, MUST create a detached and locked worktree under `.repopilot/worktrees/<worktree_id>`, and MUST NOT accept user-controlled Git arguments, worktree paths, branches, or commit-ish values.

#### Scenario: Approved patch flow creates a detached locked worktree

- **WHEN** a valid confirmed patch flow satisfies worktree preconditions
- **THEN** the system creates a detached locked worktree
- **AND** the worktree path is repo-local under `.repopilot/worktrees/`

### Requirement: Worktree Creation Checks Repository Preconditions

系统 SHALL require the target repository to be a non-bare Git repository with a valid `HEAD`, with `.repopilot/` ignored by Git, and with no tracked changes or non-ignored untracked files in the main working tree.

Ignored files MAY exist and MUST NOT block worktree creation.

#### Scenario: Dirty main workspace blocks worktree creation

- **WHEN** the main working tree has tracked changes or non-ignored untracked files
- **THEN** the system MUST refuse to create a worktree
- **AND** it MUST NOT apply the patch

### Requirement: Patch Flows Run Inside The Worktree

系统 SHALL route standalone patch apply and combined Patch + Verify through a worktree execution repo path. `patch_apply` and combined `verification_run` MUST execute against the isolated execution repo path, while standalone verification MUST continue to use the original request repo path.

The internal execution repo path MUST NOT be exposed in `/chat` top-level fields, `tool_calls`, `ToolInvocationContext`, or persistent audit payloads.

#### Scenario: Standalone verification keeps current workspace behavior

- **WHEN** the user runs a standalone verification request
- **THEN** the system MUST use the original request repo path
- **AND** it MUST NOT create a worktree first

### Requirement: Worktree And Patch State Remain Explicit

系统 SHALL persist repo-local worktree state in `.repopilot/worktrees.sqlite3`, scoped by `user_id + repo_key`. The store MUST keep safe lifecycle metadata including `worktree_id`, `patch_id`, `base_commit`, lifecycle status, verification label/status, changed-file summaries, and timestamps.

Patch apply success inside a worktree MUST transition the patch to `applied_in_worktree`. Worktree creation failure MUST leave the patch `pending`. Patch apply failure inside a worktree MUST transition the patch to `failed`. Verification failure after successful apply MUST leave the patch in `applied_in_worktree`.

#### Scenario: Verification failure preserves applied-in-worktree state

- **WHEN** a patch succeeds inside a worktree and the follow-up verification fails
- **THEN** the patch remains `applied_in_worktree`
- **AND** the worktree remains available for inspection

### Requirement: Worktree Status Queries Are Read-Only

系统 SHALL support read-only scoped inventory and detailed inspection through existing `/chat.answer`. V21 inspection replaces the V20 narrow per-id status behavior while preserving the existing status command phrases.

Missing worktree stores, empty scopes, unknown ids, missing directories, and Git registry inconsistencies MUST NOT create or modify repo-local state. Inspection answers MAY include safe identifiers, lifecycle metadata, verification summary, tracked-change statistics, consistency findings, and bounded safe preview. They MUST NOT expose local absolute paths, `.git` paths, DB paths, raw Git output, raw diff, secrets, or untracked file names.

#### Scenario: Missing worktree store query does not create state

- **WHEN** a user asks for inventory or inspection and `.repopilot/worktrees.sqlite3` does not exist
- **THEN** the system returns an empty or not-found answer
- **AND** it MUST NOT create `.repopilot` or the worktree store

### Requirement: Retained Worktrees May Be Re-verified Without Patch Mutation

系统 SHALL allow an existing scoped retained worktree to be explicitly re-verified after fail-closed consistency preflight.

Executed success SHALL use `verification_succeeded`; executed non-success SHALL use `verification_failed`. Preflight or approval failure MUST preserve the previous lifecycle. The associated patch MUST remain `applied_in_worktree` in all cases, and no `verification_rerun_*` lifecycle SHALL be added.

#### Scenario: Preflight failure preserves retained state

- **WHEN** a retained worktree fails consistency preflight
- **THEN** verification does not run
- **AND** the previous worktree lifecycle and patch state remain unchanged

### Requirement: Retained Worktrees Have Explicit Disposal Terminal States

系统 SHALL use `disposal_failed` to represent a partially completed disposal requiring explicit reconciliation and `discarded` to represent confirmed worktree cleanup terminal state.

Eligible retained worktrees MAY transition to these states only through V23 confirmed disposal/reconciliation. A disposed worktree MUST NOT be treated as eligible for inspection-derived execution, re-verification, patch mutation, or promotion.

#### Scenario: Disposed worktree is terminal

- **WHEN** a worktree reaches `discarded`
- **THEN** repeated disposal/reconciliation is idempotent
- **AND** re-verification MUST reject the worktree
