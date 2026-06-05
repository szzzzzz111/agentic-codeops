## MODIFIED Requirements

### Requirement: Stage Debt Sweep Is A Checkable Gate

系统 SHALL require an explicit Stage Debt Sweep before a stage is called implementation-complete, ready to commit, archive-ready, merged, pushed, or ready for the next stage.

The Stage Debt Sweep MUST scan current durable docs, harness docs, active OpenSpec artifacts, long-term specs, changed runtime paths, and adjacent older runtime paths. Discoverable debt MUST be fixed in scope or recorded as a blocker in durable docs. It MUST NOT remain only in chat.

#### Scenario: Stage Debt Sweep evidence is durable

- **WHEN** a stage reaches review or closeout
- **THEN** `docs/PROGRESS.md`, `HANDOFF_TO_NEXT_CHAT.md`, and `.harness/review_checklist.md` include checkable Stage Debt Sweep evidence or blockers

### Requirement: Post-Merge Durable Docs Reflect Actual State

系统 SHALL update durable docs after merge/push with the actual main/remote state, commit hash, validation evidence, next stage recommendation, and feature branch cleanup/retention decision.

#### Scenario: Merge/push closeout does not leave stale next steps

- **WHEN** a stage has been merged and pushed
- **THEN** durable docs MUST NOT continue to describe merge/push as a future decision for that completed stage
- **AND** durable docs MUST record whether the feature branch was retained or cleaned up

### Requirement: Process Skills Are Not Runtime Capabilities

系统 SHALL treat local `.codex/skills/**` edits as development process documentation only unless a future stage explicitly makes a runtime capability. V19 MUST NOT describe Stage Debt Sweep, handoff skills, OpenSpec skills, Superpowers, MCP, or plugins as RepoPilot runtime behavior.

#### Scenario: Skill boundary remains process-only

- **WHEN** `.codex/skills/repo-stage-review-loop/SKILL.md` or `.codex/skills/repo-stage-handoff/SKILL.md` is edited during V19
- **THEN** the change is documented as process discipline only
- **AND** runtime docs MUST NOT list it as a product feature
