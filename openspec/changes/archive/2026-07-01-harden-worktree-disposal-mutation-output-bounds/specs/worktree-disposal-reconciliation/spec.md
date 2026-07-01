## MODIFIED Requirements

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
