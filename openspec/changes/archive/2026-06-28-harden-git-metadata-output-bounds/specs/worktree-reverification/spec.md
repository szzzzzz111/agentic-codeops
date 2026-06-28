## MODIFIED Requirements

### Requirement: Re-verification Uses Hardened Metadata And Rejects Disposal States

系统 SHALL use the shared timeout-aware pre-read-bounded Git metadata runner for re-verification preflight.

`disposal_failed` and `discarded` worktrees MUST be ineligible for re-verification. Metadata timeout, stdout oversize, reader failure, non-zero exit, malformed output, or exception MUST fail closed without retry or verification execution.

#### Scenario: Disposed worktree cannot be re-verified

- **WHEN** a scoped worktree is already `discarded`
- **THEN** re-verification rejects it before executing verification

#### Scenario: Oversize metadata blocks re-verification

- **WHEN** a Git metadata command used by re-verification preflight exceeds the configured output cap
- **THEN** re-verification fails closed before `verification_run`
- **AND** no raw Git output is exposed
