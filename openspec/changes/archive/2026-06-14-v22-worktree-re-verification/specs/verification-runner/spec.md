## ADDED Requirements

### Requirement: Verification Runner Supports Trusted Retained Worktree Execution

系统 SHALL allow V22 retained worktree re-verification to reuse `ToolExecutor.verification_run` only after scoped fail-closed preflight has produced a trusted internal execution path.

The existing whitelist, argv, permission/approval context, timeout, output limits, and redaction MUST remain unchanged. The trusted execution path MUST NOT be exposed or persisted.

#### Scenario: Existing whitelist remains authoritative

- **WHEN** retained worktree re-verification requests an unsupported label or additional arguments
- **THEN** the system rejects the request
- **AND** it MUST NOT call the Verification Runner
