## ADDED Requirements

### Requirement: V20 Preserves Main Workspace Semantics

V20 SHALL isolate RepoPilot-owned patch mutation from the user's main working tree while preserving standalone verification semantics. Standalone verification MUST continue to inspect the current repository working tree and MUST NOT be forced into an isolated worktree.

#### Scenario: Standalone verification remains main-worktree scoped

- **WHEN** the user sends an explicit standalone verification request
- **THEN** the system runs verification against the request repo path
- **AND** it MUST NOT create a worktree first
