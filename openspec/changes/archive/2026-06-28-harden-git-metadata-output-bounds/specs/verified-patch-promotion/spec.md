## MODIFIED Requirements

### Requirement: Promotion Is Explicit, Scoped, And Fail-Closed

系统 SHALL allow promotion only for the current `user_id + repo_key` scoped retained worktree whose worktree lifecycle is `verification_succeeded` and whose patch status is `applied_in_worktree`. It MUST check main workspace cleanliness, main `HEAD == base_commit`, expected worktree path, Git registry/lock, linked-worktree ownership, retained worktree `HEAD == base_commit`, stored diff hash, and target content integrity. Any exception or mismatch MUST fail before main workspace writes.

Promotion preflight MUST use the shared hardened Git metadata runner for main workspace and retained worktree metadata reads. Metadata timeout, stdout oversize, reader failure, non-zero exit, malformed output, or exception MUST fail closed before promotion begins and MUST NOT expose raw Git output.

#### Scenario: Ineligible worktree is rejected

- **WHEN** a retained worktree is not `verification_succeeded`
- **THEN** promotion fails before any main workspace write

#### Scenario: Oversize metadata blocks promotion

- **WHEN** a Git metadata command used by promotion preflight exceeds the configured output cap
- **THEN** promotion fails closed before `patch_apply`
- **AND** no raw Git output is exposed
