## ADDED Requirements

### Requirement: Re-verification Uses Hardened Metadata And Rejects Disposal States

系统 SHALL use the shared timeout-aware pre-read-bounded Git metadata runner for re-verification preflight.

`disposal_failed` and `discarded` worktrees MUST be ineligible for re-verification. Metadata timeout, oversize, malformed output, or exception MUST fail closed without retry or verification execution.

#### Scenario: Disposed worktree cannot be re-verified

- **WHEN** a user requests re-verification for a scoped `discarded` worktree
- **THEN** preflight rejects the request
- **AND** verification MUST NOT run
