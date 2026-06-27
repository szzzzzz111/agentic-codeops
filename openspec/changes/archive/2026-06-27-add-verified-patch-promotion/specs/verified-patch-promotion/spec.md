## ADDED Requirements

### Requirement: Promotion Requires Explicit Confirmation And Current Scope

系统 SHALL accept Verified Patch Promotion only through an exact explicit confirmation command for a worktree id in the current `user_id + repo_key` scope.

Missing confirmation, partial matches, extra text, unsafe ids, user-controlled paths, Git argv, branch names, commit-ish values, environment variables, pipes, redirects, shell syntax, remote names, PR hints, and ambiguous continuation language MUST be rejected as a whole. Rejected promotion-like requests MUST NOT fall through to repo search, patch apply, verification, disposal, commit, merge, push, branch, or PR behavior.

#### Scenario: Missing confirmation is rejected

- **WHEN** a user sends `promote worktree wt_abc`
- **THEN** the system rejects the recognized promotion-like request
- **AND** it MUST NOT inspect Git, apply a patch, perform business state mutation beyond a safe recognized-attempt audit, or fall through

### Requirement: Promotion Eligibility Fails Closed

系统 SHALL resolve promotion eligibility only from scoped worktree and patch metadata in the current `user_id + repo_key`.

Promotion MUST require an existing retained worktree with lifecycle `verification_succeeded`, related patch status `applied_in_worktree`, clean main workspace, main workspace `HEAD == base_commit`, expected worktree path consistency, Git registry consistency, linked-worktree ownership consistency, retained worktree `HEAD == base_commit`, and valid stored patch identity.

Any missing, cross-scope, stale, dirty, mismatched, malformed, unavailable, or exceptional condition MUST fail before main workspace mutation.

#### Scenario: Base drift blocks promotion

- **WHEN** the main workspace `HEAD` differs from the retained worktree metadata `base_commit`
- **THEN** promotion fails closed
- **AND** the system MUST NOT call `patch_apply`

### Requirement: Promotion Routing Is Distinct

系统 SHALL route recognized promotion-like requests after worktree disposal/reconciliation and before retained worktree re-verification, patch handling, standalone verification, audit recovery, capability status, and repo-search fallback.

Malformed promotion-like requests MUST be rejected by the promotion route and MUST NOT fall through to later routes.

#### Scenario: Promotion-like request does not fall through

- **WHEN** a user sends a malformed promotion-like worktree request
- **THEN** AgentLoop rejects it in the promotion route
- **AND** it MUST NOT run re-verification, patch handling, standalone verification, audit recovery, or repo search

### Requirement: Promotion Validates Stored Patch Integrity Before Writing

系统 SHALL validate that the retained worktree target file contents match the expected result of the stored original controlled patch before promotion writes the main workspace.

The system MUST NOT trust the retained worktree's current files as the write source and MUST NOT directly copy files from the worktree into the main workspace. The main workspace write MUST be derived from the stored controlled patch.

#### Scenario: Tampered worktree content is rejected

- **WHEN** the retained worktree target file no longer matches the expected result of the stored patch
- **THEN** promotion fails closed
- **AND** the main workspace remains unchanged

### Requirement: Promotion Reuses The Existing Patch Apply Harness Boundary

系统 SHALL perform any accepted main workspace write through the existing approval-gated `patch_apply` boundary, using `ToolRegistry`, `PermissionPolicy`, `ApprovalGate`, and `ToolExecutor`.

Promotion MUST NOT bypass `patch_apply`, MUST NOT copy worktree files, and MUST NOT accept user-controlled cwd, paths, argv, timeout, environment, or patch text.

Promotion MUST use a distinct promotion-safe permission context. The system MUST NOT broaden ordinary patch confirmation so that any `applied_in_worktree` patch can be applied again without full promotion preflight.

#### Scenario: Promotion uses patch_apply

- **WHEN** a verified retained worktree passes all promotion preflight checks
- **THEN** the system invokes the approved `patch_apply` execution path against the main workspace using the stored patch
- **AND** it MUST NOT invoke filesystem copy from the retained worktree

#### Scenario: Bare applied-in-worktree patch apply remains rejected

- **WHEN** a patch has status `applied_in_worktree` but no successful promotion preflight context exists
- **THEN** permission/approval MUST reject direct `patch_apply`
- **AND** the main workspace remains unchanged

### Requirement: Promotion State Transitions Are Explicit And Non-Automating

系统 SHALL update patch, worktree, and audit state only after the selected promotion step has succeeded according to the V25 state machine.

Successful promotion SHALL transition the patch and worktree to explicit `promoted` states. Preflight failure, approval failure, and execution failure MUST NOT mark the patch or worktree promoted. Promotion MUST NOT leave the main workspace partially promoted, and implementation MUST prove or provide a promotion-safe atomic/staged write mechanism before enabling the command. Promotion MUST NOT delete, discard, reconcile, unlock, prune, retry, repair, commit, merge, push, create branches, create PRs, or schedule background follow-up.

The only V25 promotion success transition is `verification_succeeded` worktree plus `applied_in_worktree` patch to `promoted` worktree plus `promoted` patch. Repeat promotion of an already `promoted` worktree MUST be rejected as a safe no-op. `promoted` worktrees MUST NOT be eligible for re-verification, re-promotion, patch mutation, or V23 disposal in V25.

#### Scenario: Verification failure state is ineligible

- **WHEN** a scoped retained worktree lifecycle is `verification_failed`
- **THEN** promotion is rejected
- **AND** patch and worktree state remain unchanged

#### Scenario: Repeat promotion is a safe rejection

- **WHEN** a scoped retained worktree is already `promoted`
- **THEN** promotion is rejected without mutation
- **AND** the patch and worktree remain `promoted`

#### Scenario: Write failure does not partially promote

- **WHEN** promotion write execution fails before a complete promoted state can be recorded
- **THEN** the main workspace remains unchanged or is safely restored
- **AND** patch and worktree MUST NOT be marked `promoted`

### Requirement: Promotion Attempts Are Safely Auditable

系统 SHALL attempt to persist one scoped redacted promotion audit event for every recognized promotion-like request, related to the worktree id and patch id when safely known.

The event MAY include confirmation, preflight classification, execution-attempted flag, safe state transition, and safe error class. Public output and audit payloads MUST NOT contain local absolute paths, `.git` paths, DB paths, raw Git output, full diff, patch body, copied file content, environment variables, secrets, raw exception text, or unknown directory names.

#### Scenario: Preflight failure is auditable without mutation

- **WHEN** a recognized promotion request fails eligibility preflight
- **THEN** one safe audit event records that execution was not attempted
- **AND** no main workspace mutation occurs

### Requirement: Promotion Reuses The Existing Chat Contract

系统 SHALL return promotion results through existing `/chat.answer` and safe `tool_calls` semantics.

Promotion MUST NOT add required or optional `/chat` top-level fields, MUST NOT add a standalone promotion API, and MUST NOT expose the trusted retained worktree path.

#### Scenario: Promotion answer keeps response schema

- **WHEN** `/chat` returns a promotion result
- **THEN** the response still contains only `trace_id`, `answer`, `related_files`, and `tool_calls`
- **AND** the answer does not expose local absolute paths or raw Git output
