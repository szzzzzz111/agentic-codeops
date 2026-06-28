## MODIFIED Requirements

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
