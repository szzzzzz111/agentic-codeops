## ADDED Requirements

### Requirement: V24 CLI Surface Replaces Previous Promotion Slot

RepoPilot SHALL treat V24 as the CLI Capability Surface / Demo-ready Product Surface stage. The previous Verified Patch Promotion roadmap item MUST be moved to V25 or backlog and MUST NOT be implemented or documented as implemented by this stage.

#### Scenario: V24 planning updates roadmap truth

- **WHEN** V24 CLI Capability Surface planning artifacts and docs are updated
- **THEN** README, ARCHITECTURE, PROGRESS, HANDOFF, and relevant specs MUST avoid using V24 to mean Verified Patch Promotion
- **AND** Verified Patch Promotion MUST be described only as a future candidate

### Requirement: Plan Review Gates Precede Implementation

Medium and high risk RepoPilot stages SHALL complete plan-level review before runtime or test implementation begins.

Plan-level review MUST include internal plan review, Codex independent plan review, OpenCode independent plan review, and triage of all findings. Passing OpenSpec validation MUST NOT be treated as plan review.

#### Scenario: Implementation waits for plan review evidence

- **WHEN** a medium or high risk stage reaches the implementation confirmation gate
- **THEN** internal plan review MUST check proposal, design, tasks, spec deltas, test plan, and Harness boundaries
- **AND** Codex independent plan review MUST return severity findings or an explicit no-findings conclusion
- **AND** OpenCode independent plan review MUST return final assistant review text with severity findings or an explicit no-findings conclusion
- **AND** all plan findings MUST be classified as `fix`, `clarify`, `reject`, or `defer`

#### Scenario: OpenCode review terminal timeout is not a verdict

- **WHEN** an `opencode run` review command times out or does not print a final result
- **THEN** the agent MUST inspect the relevant OpenCode session for final assistant review text before marking the gate failed
- **AND** missing final review text remains a blocker unless the user explicitly authorizes a downgrade

#### Scenario: OpenCode review prefers existing review sessions

- **WHEN** an OpenCode plan review is required
- **THEN** the agent SHOULD run `opencode session list` to find a relevant existing review session
- **AND** it SHOULD use `opencode run --session <session_id> ...` before creating a new session
- **AND** the final review evidence MUST identify whether the session was reused or newly created

### Requirement: External Review Triage Covers Plans

External review triage SHALL apply to plan findings as well as implementation findings.

#### Scenario: Plan reviewer reports findings

- **WHEN** Codex, OpenCode, or another external reviewer reports plan findings
- **THEN** each finding MUST be classified as `fix`, `clarify`, `reject`, or `defer`
- **AND** accepted fixes or clarifications MUST be reflected in the plan before implementation begins
