# worktree-disposal-reconciliation Specification

## Purpose
Define explicit, scoped, fail-closed disposal and narrow reconciliation for retained worktrees, including ordered lifecycle closeout and redacted persistent audit.
## Requirements
### Requirement: Worktree Disposal And Reconciliation Require Exact Confirmation

系统 SHALL accept only exact `confirm discard worktree <worktree_id>`, `确认丢弃 worktree <worktree_id>`, `confirm reconcile worktree <worktree_id>`, and `确认协调 worktree <worktree_id>` requests.

The full normalized request MUST match. Missing confirmation, extra text, user-controlled paths/arguments, shell syntax, and partial matches MUST be rejected as a whole. Discussion such as `how to discard changes` MUST NOT be treated as disposal intent.

#### Scenario: Missing confirmation is rejected

- **WHEN** a user sends `discard worktree wt_abc`
- **THEN** the system rejects the recognized disposal-like request
- **AND** it MUST NOT unlock, remove, delete, update state, or fall through

### Requirement: Disposal Preflight Is Scoped And Fail-Closed

系统 SHALL resolve worktree and patch metadata only in the current `user_id + repo_key` scope and SHALL reconstruct the expected directory only from trusted repo root, fixed managed root, and validated scoped worktree id.

Normal disposal MUST require lifecycle `patch_applied`, `verification_failed`, or `verification_succeeded`, exact registry path, safe linked-worktree ownership, directory presence, and `HEAD == base_commit`. The system MUST reject unknown/cross-scope ids, damaged metadata, unsupported lifecycle, path mismatch, HEAD mismatch, main workspace, managed root, outside path, symlink/reparse point, and unknown ownership before mutation.

Linked-worktree ownership MUST require a regular non-symlink `.git` file, expected-directory top-level identity, original-repo common Git directory identity, an administrative target under that common directory's `worktrees/` root, and an exact administrative `gitdir` back-reference. Before destructive mutation, the associated scoped patch MUST exist with status `applied_in_worktree`; complete idempotent or patch-only closeout MAY accept `discarded`.

All Git metadata reads used by disposal and reconciliation preflight MUST use the shared hardened metadata runner. Metadata timeout, oversized stdout, reader failure, non-zero exit, malformed output, or exception MUST fail closed before mutation and MUST NOT expose raw Git output.

#### Scenario: Unknown directory ownership is rejected

- **WHEN** the expected directory exists but linked-worktree ownership cannot be proven
- **THEN** disposal and reconciliation fail closed
- **AND** the directory MUST NOT be deleted

#### Scenario: Oversize preflight metadata fails before mutation

- **WHEN** a Git metadata command used by disposal or reconciliation preflight exceeds the configured output cap
- **THEN** the metadata runner kills and reaps the process when possible
- **AND** disposal and reconciliation fail closed before unlock, remove, delete, or state transition
- **AND** no raw Git output is exposed

### Requirement: Reconciliation Is Limited To Safe Disposal Residuals

系统 SHALL allow confirmed reconciliation only for a safe residual set: both directory and registry missing, directory missing with exact registry entry, registry missing with ownership-attested matching directory, both present after a prior successful unlock, or `discarded` worktree metadata with a scoped patch not yet `discarded`.

Path, HEAD/base, metadata, scope, or ownership uncertainty MUST NOT be repaired. The system MUST NOT run `git worktree prune`, implicitly reconcile, or automatically retry.

#### Scenario: Directory missing registry present can be reconciled

- **WHEN** scoped metadata and exact registry entry remain but the expected directory is missing
- **THEN** confirmed reconciliation MAY unlock only when locked and remove the exact registry entry
- **AND** it MUST NOT affect any other worktree

### Requirement: Disposal Uses Strict Ordered Idempotent Execution

系统 SHALL execute accepted disposal only through the approval-gated `worktree_dispose` Harness path. Normal order MUST be optional unlock, exact worktree remove, absence post-check, scoped worktree `discarded`, then scoped patch `discarded`.

Any step failure MUST stop immediately without retry or rollback of completed destructive steps. Complete repeated disposal/reconciliation MUST return idempotent success without destructive operations.

Destructive Git mutation subprocesses used for unlock/remove MUST use fixed argv, `shell=False`, `GIT_OPTIONAL_LOCKS=0`, an independent timeout, and independent stdout/stderr hard caps enforced before output bytes are retained, decoded, logged, or exposed. Timeout, stdout/stderr oversize, reader failure, reader non-completion, or non-zero exit after process start MUST kill and/or bounded-reap when possible, then fail the current mutation step with a safe mutation failure; process-start failure MUST fail the current mutation step safely without requiring process cleanup that cannot exist. Raw Git output, stderr, exception text, local absolute paths, DB paths, secrets, patch body, and diff content MUST NOT be exposed in public or audit output.

#### Scenario: Patch update follows worktree terminal state

- **WHEN** the worktree has not been confirmed absent and recorded `discarded`
- **THEN** the associated patch MUST NOT transition to `discarded`

#### Scenario: Oversize mutation output fails current step safely

- **WHEN** an unlock or remove Git mutation emits stdout or stderr beyond the configured cap
- **THEN** disposal kills and bounded-reaps the mutation process when possible
- **AND** disposal reports a safe `mutation_failed` outcome for the current step
- **AND** no raw Git output is exposed

### Requirement: Disposal Lifecycle And Partial Failures Remain Explicit

系统 SHALL add worktree lifecycle states `disposal_failed` and `discarded`, and patch terminal state `discarded`.

Mutation-before failure MUST preserve prior state. Unlock/remove/post-check failure MAY set scoped worktree `disposal_failed` while preserving patch state. If patch update fails after worktree becomes `discarded`, the worktree MUST remain `discarded` and later confirmed reconciliation MAY perform patch-only closeout.

#### Scenario: Patch-only reconciliation completes terminal state

- **WHEN** scoped worktree metadata is `discarded` but its scoped patch remains `applied_in_worktree`
- **THEN** confirmed reconciliation updates only the patch to `discarded`
- **AND** it MUST NOT execute Git or directory deletion

### Requirement: Every Disposal Attempt Is Safely Auditable

系统 SHALL attempt to persist one scoped redacted `worktree_disposal` event for every recognized discard/reconcile attempt, related to the requested worktree id.

The event SHALL distinguish attempt kind, confirmation, preflight classification, completed step, failed step, and safe worktree/patch terminal state. Public and audit output MUST NOT include absolute paths, raw Git output, DB paths, environment variables, secrets, diff, patch body, or unknown directory names.

#### Scenario: Rejected attempt remains auditable

- **WHEN** a recognized disposal-like request lacks confirmation or fails preflight
- **THEN** one safe attempt event records that mutation was not executed
- **AND** no destructive operation occurs

### Requirement: V23 Does Not Dispose Promoted Worktrees

V23 disposal/reconciliation SHALL reject `promoted` worktrees and MUST NOT delete the retained worktree or transition its `promoted` patch to `discarded`.

#### Scenario: Promoted worktree cannot be discarded

- **WHEN** V23 disposal targets a scoped `promoted` worktree
- **THEN** it rejects without cleanup or patch status change
