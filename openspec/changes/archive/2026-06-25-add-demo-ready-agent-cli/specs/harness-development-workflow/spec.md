## ADDED Requirements

### Requirement: CLI Implementation Stays Inside Existing Runtime Boundaries

The Demo-ready Agent CLI implementation SHALL be planned and reviewed as a medium-risk user-facing command surface.

It MUST use TDD, update Harness boundaries before runtime/test edits, and preserve existing `/chat`, AgentLoop, ToolExecutor, PermissionPolicy, ApprovalGate, VerificationRunner, Worktree, Audit, provider, and CI boundaries. It MUST NOT introduce V24 promotion, arbitrary shell execution, network dependency, background tasks, subagents, connectors, commit/merge/push automation, or real model patch provider wiring.

#### Scenario: CLI implementation starts after planning gate

- **WHEN** `add-demo-ready-agent-cli` planning artifacts validate successfully
- **THEN** implementation remains blocked until explicit confirmation
- **AND** allowed files and review checklist define the CLI runtime/test/doc scope

#### Scenario: CLI closeout requires command-surface review

- **WHEN** CLI implementation is complete
- **THEN** review MUST check parser safety, command mapping, exit codes, output redaction, no new network dependency, no `/chat` contract change, and no bypass of existing patch/verification confirmation boundaries
