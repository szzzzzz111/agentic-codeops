## ADDED Requirements

### Requirement: Material stage changes reopen the exact dependent gates
For stages newly created in an explicitly host-activated v2 cohort, when implementation, review, repository state, or a direct-user instruction changes an already closed or bound stage fact, the RepoPilot development workflow MUST stop the affected action, compare against the host gate snapshot and immutable workspace binding, CAS-append a canonical change event, recompute the conservative V1 suffix/prefix sets, and resume only at the exact current frontier. A governed mutation earlier or later than the frontier MUST fail; it MUST NOT proceed merely because its gate is called unaffected. Ordinary planned edits while their initial gate is mechanically open, and archive/candidate/merge/push outputs, use the no-event path only when a code-owned transition adapter proves exact pre-state/delta/post-state. Gate completion MUST use code-owned evidence adapters rather than arbitrary repository PASS files. The workflow MUST use a replay frontier set rather than a fixed resume step. This introducing stage and every stage already in flight at later activation remain pre-change v1 cohorts through terminal. Until a separately reviewed `provider_neutral.stage_state_cas/v1` host implementation is active, replay validation is dormant/mechanical-only and MUST NOT authorize or block mutation.

#### Scenario: Requirement changes during implementation
- **WHEN** the user changes a requirement, scope item, non-goal, risk boundary, or allowed file family after plan approval
- **THEN** implementation MUST stop before using the old plan or authority
- **AND** the workflow MUST update OpenSpec/Harness facts, obtain any required later authority epoch, repeat applicable plan review, and replay downstream gates from the computed frontier

#### Scenario: Technical remediation stays in scope
- **WHEN** a review finding requires an implementation/test correction that remains inside the confirmed envelope
- **THEN** the workflow MUST invalidate affected verification, implementation review, and downstream delivery evidence
- **AND** it MUST NOT ask the product owner to approve an Agent-owned technical choice unless the correction changes the owner-bound envelope

#### Scenario: Unrelated evidence remains valid
- **WHEN** a material change leaves a gate's direct inputs, dependency closure, artifact hashes, authority binding, and Git facts unchanged
- **THEN** V1 MAY retain only the exact prefix before the earliest seed
- **AND** the host snapshot and evidence adapter MUST record the exact unchanged-input proof

#### Scenario: Final packet is followed by a new material change
- **WHEN** any material event or non-tail repository change occurs after the final delivery packet is frozen
- **THEN** the packet, affected verification, final review, archive readiness, candidate, merge, and push readiness MUST become stale
- **AND** the event/replay record MUST enter the next reviewed subject rather than extend the two-file evidence tail

#### Scenario: Stage is already pushed and verified
- **WHEN** the same-endpoint remote query has verified the exact candidate on the target branch and the stage is closed
- **THEN** the host terminal tombstone MUST reject same-stage event/apply requests with `NEW_STAGE_REQUIRED`
- **AND** a later product or workflow request MUST start a new stage
- **AND** it MUST NOT be appended as a change event that silently reopens or extends the closed stage

#### Scenario: Host capability has not been activated
- **WHEN** repository validators, templates, or skills exist but no separately reviewed host CAS/recovery/dispatch implementation and activation chronology exist
- **THEN** Codex/OpenCode entrypoints MUST keep the pre-change gate authoritative
- **AND** a CLI, fixture, handoff, receipt, or activation hash MUST NOT convert replay into a blocking gate

#### Scenario: Stage runs in a different worktree
- **WHEN** the same stage bytes and planning base appear in a sibling clone, linked worktree, or symlinked root that differs from the host-issued workspace binding
- **THEN** replay state MUST NOT be reused in that workspace
