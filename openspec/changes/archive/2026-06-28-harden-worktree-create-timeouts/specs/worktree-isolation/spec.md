## ADDED Requirements

### Requirement: Worktree Creation Git Calls Are Timeout-Bounded

Worktree creation and rollback SHALL execute local Git subprocesses with fixed argv, `shell=False`,
`GIT_OPTIONAL_LOCKS=0`, an independent timeout, and hard caps on stdout and stderr before content is decoded or used.
The manager-local defaults SHALL be `WORKTREE_GIT_TIMEOUT_SECONDS = 10.0` and
`WORKTREE_GIT_OUTPUT_MAX_BYTES = 256_000` per stream.

Timeout, output oversize, process start failure, non-zero exit, or subprocess error MUST fail closed using existing
safe worktree creation failure semantics. Public answers, tool calls, and persistent audit MUST NOT expose raw stdout,
raw stderr, raw exception text, traceback, local absolute paths, `.git` paths, or DB paths from these failures.

`git check-ignore` is the only create preflight command whose non-zero exit may be business data: return code `1`
SHALL mean `.repopilot/` is not ignored, while return codes greater than `1`, timeout, output oversize, or subprocess
errors SHALL use safe creation failure semantics.

Rollback Git commands for failed creation MUST use the same timeout and output bounds and remain best-effort; rollback
failure MUST NOT hang the primary flow or convert an unsafe partial create into a successful create result.

#### Scenario: Worktree create subprocess timeout fails closed

- **WHEN** a Git subprocess used by worktree creation or preflight does not finish before the configured timeout
- **THEN** the process is killed and reaped when possible
- **AND** worktree creation returns a safe failure result
- **AND** no patch is applied and no raw process output is exposed

#### Scenario: Rollback subprocess timeout remains best-effort

- **WHEN** worktree creation fails after a worktree path may have been created
- **AND** a rollback Git subprocess times out or fails
- **THEN** rollback continues with remaining best-effort cleanup
- **AND** create still returns a safe failure result rather than hanging or reporting success
