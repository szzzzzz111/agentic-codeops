## ADDED Requirements

### Requirement: V23 Planning And Implementation Remain Separately Confirmed

V23 SHALL complete stage planning, OpenSpec artifacts, harness synchronization, internal plan review, and strict OpenSpec validation before runtime or test implementation begins.

The implementation MUST remain limited to explicit worktree disposal/reconciliation and blocking adjacent metadata/store hardening. It MUST NOT include promotion, patch mutation/reapply, implicit repair, automatic retry, commit, merge, push, arbitrary shell, background tasks, subagents, connectors, or frontend behavior.

#### Scenario: Planning stops before implementation

- **WHEN** V23 planning artifacts pass internal review and validation
- **THEN** the stage stops at the implementation confirmation gate
- **AND** runtime code and tests remain unchanged until explicit confirmation
