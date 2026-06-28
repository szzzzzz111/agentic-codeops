## ADDED Requirements

### Requirement: Workflow Skills Keep Specification And Execution Roles Separate

RepoPilot repo-local workflow skills SHALL distinguish specification baseline work from execution discipline.
OpenSpec SHALL own requirement clarification, interface/model/design decisions, task decomposition, spec review,
requirement changes, and archive. Execution-discipline skills SHALL own reading the approved baseline,
isolated development where needed, TDD, deterministic verification, code review, finishing, and skill/process
self-checks.

Workflow documentation MUST NOT describe OpenSpec, Superpowers, Codex/OpenCode skills, MCP, plugins, or
connectors as RepoPilot runtime capabilities unless a future runtime OpenSpec change explicitly opens that scope.

#### Scenario: Requirement changes during implementation

- **WHEN** implementation reveals a requirement change, design contradiction, or scope drift
- **THEN** the workflow returns to OpenSpec planning or exploration before implementation resumes
- **AND** the execution plan is regenerated or updated from the new approved baseline

#### Scenario: Process-only workflow update

- **WHEN** a change edits only repo-local workflow skills and owned process documents
- **THEN** risk may be classified as low
- **AND** validation and review focus on process clarity, scope truth, roadmap truth, and document ownership
- **AND** runtime files and public product contracts remain out of scope
