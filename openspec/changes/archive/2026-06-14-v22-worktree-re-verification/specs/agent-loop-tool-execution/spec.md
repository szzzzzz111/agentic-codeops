## ADDED Requirements

### Requirement: Agent Loop Routes Worktree Re-verification Before Standalone Verification

系统 SHALL handle explicit retained worktree re-verification after worktree inventory/inspection and before patch, standalone verification, audit recovery, capability status, and repo-search fallback.

The route MUST NOT call repo RAG, patch apply, cleanup, reconciliation, promotion, or any tool other than the approved existing `verification_run` after successful preflight.

#### Scenario: Re-verification is not swallowed by standalone verification

- **WHEN** a user sends `worktree verify <worktree_id> verify`
- **THEN** AgentLoop handles retained worktree re-verification
- **AND** it MUST NOT run standalone verification against the request repo path
