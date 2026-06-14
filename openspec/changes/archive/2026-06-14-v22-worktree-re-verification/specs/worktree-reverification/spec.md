## ADDED Requirements

### Requirement: Retained Worktree Re-verification Is Explicit And Whitelisted

系统 SHALL accept only explicit `worktree verify <worktree_id> <command_label>` and `重新验证 worktree <worktree_id> <command_label>` requests for retained worktree re-verification.

The complete normalized request MUST match the command shape, and `command_label` MUST reuse the existing `pytest`, `ruff`, or `verify` whitelist. User-provided arguments, paths, environment variables, pipes, redirection, shell syntax, unknown labels, and partial matches MUST be rejected before Git inspection or verification execution. Rejected re-verification-like requests MUST NOT fall through to standalone verification or repo-search fallback.

#### Scenario: Extra arguments are rejected

- **WHEN** a user sends `worktree verify wt_abc pytest -k test_name`
- **THEN** the system rejects the request
- **AND** it MUST NOT inspect Git or run verification
- **AND** it MUST NOT run standalone verification or repo search

### Requirement: Re-verification Preflight Fails Closed

系统 SHALL resolve worktree metadata only within the current `user_id + repo_key` scope and SHALL derive the expected worktree directory only from trusted scoped metadata and the managed worktree root.

Before verification, the system MUST require lifecycle `patch_applied`, `verification_failed`, or `verification_succeeded`, then confirm that the expected directory exists, Git registry contains the worktree, registry path matches the expected directory, and worktree HEAD equals metadata `base_commit`. `ready`, `create_failed`, `patch_failed`, and unknown lifecycle values MUST fail before Git inspection.

Any missing, inconsistent, malformed, unavailable, or exceptional preflight condition MUST fail closed. The system MUST NOT run verification, repair metadata, reconcile state, cleanup, unlock/remove, retry Git, create an unknown worktree, or modify the main workspace.

#### Scenario: HEAD mismatch blocks execution

- **WHEN** scoped metadata exists but the worktree HEAD differs from `base_commit`
- **THEN** the system returns a safe preflight failure
- **AND** it MUST NOT call `verification_run`

### Requirement: Re-verification Runs Only Inside The Retained Worktree

系统 SHALL execute accepted re-verification only through `ToolRegistry`, `PermissionPolicy`, `ApprovalGate`, and `ToolExecutor.verification_run` using the trusted retained worktree execution path.

The system MUST reuse existing Verification Runner argv, timeout, output limits, and redaction. It MUST NOT execute verification against the main workspace or accept user-controlled cwd, argv, path, environment, or timeout.

#### Scenario: Main workspace remains unchanged

- **WHEN** a retained worktree passes preflight and re-verification executes
- **THEN** verification cwd is the retained worktree
- **AND** the main workspace remains unchanged

### Requirement: Existing Lifecycle And Patch State Are Preserved

系统 SHALL use only existing worktree lifecycle values. Successful executed re-verification SHALL set `verification_succeeded`; any executed non-success result SHALL set `verification_failed`.

Preflight or approval failure MUST preserve the previous worktree lifecycle because verification did not execute. V22 MUST NOT add `verification_rerun_*` lifecycle values.

The related patch MUST remain `applied_in_worktree` after successful verification, failed verification, or preflight rejection. Re-verification MUST NOT read, modify, or reapply the patch.

#### Scenario: Failed execution preserves patch state

- **WHEN** re-verification executes and fails
- **THEN** the worktree lifecycle becomes `verification_failed`
- **AND** the related patch remains `applied_in_worktree`

### Requirement: Every Re-verification Request Produces A Safe Attempt Audit

系统 SHALL attempt to persist one redacted scoped `verification_result` audit event for every recognized worktree re-verification request, related to the requested worktree id.

The audit SHALL include `attempt_kind=worktree_reverification` and `related_id=<worktree_id>`, and SHALL distinguish whether execution was attempted, preflight outcome, command label when safely parsed, and the safe execution result when available. Scoped matching audit event count SHALL express rerun count without a new mutable counter or schema migration.

Audit and public/request-local summaries MUST NOT contain full stdout/stderr, absolute paths, `.git` paths, DB paths, environment variables, secrets, raw Git output, diff, or preview.

#### Scenario: Preflight failure is auditable without execution

- **WHEN** a recognized re-verification request fails preflight
- **THEN** one safe audit event records `execution_attempted=false`
- **AND** verification does not run
- **AND** the previous worktree lifecycle is preserved

### Requirement: Public Re-verification Results Are Distinguishable

系统 SHALL make retained worktree re-verification answers visibly distinguishable from standalone verification answers while preserving the existing `/chat` contract.

Executed answers MUST identify the safe worktree id and command label without exposing the execution path.

#### Scenario: Executed answer identifies retained worktree

- **WHEN** worktree re-verification executes
- **THEN** the answer identifies the retained worktree and verification command
- **AND** it MUST NOT be formatted as an unqualified standalone verification result
