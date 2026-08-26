## MODIFIED Requirements

### Requirement: Material drift invalidates inherited authorization
The workflow MUST invalidate an existing authorization when stage scope, non-goals, risk, action ceiling, planning baseline identity, target remote fingerprint, target branch, or authorized remote tip changes. A replacement record MUST use a later epoch, content-hash the superseded record, and reference a new live direct-user decision covering the changed envelope. Cohort selection is an external host chronology fact, not a caller/schema choice. For this introducing stage and every in-flight v1 cohort, replacement authority before terminal MUST continue to use the existing pre-change `stage_authority/v1` producer, template, validator, epoch and supersession semantics; it MUST NOT require a replay event or reinterpret the record as v2. For a future explicitly host-activated v2 cohort only, the host-CAS accepted direct-user event SHALL first bind the superseded authority plus the required later epoch; a `stage_authority/v2` replacement record SHALL bind that trigger event count/head and supersede the old record; the later replay receipt SHALL bind event head plus new authority hash. V2 validator comparison of the old/new authority scope MUST exactly match the declared event facts. Its host controller SHALL retain the gate snapshot and exact event/receipt prior/current count/head values. A later v2 authority epoch or recomputed scope digest alone MUST NOT establish replay progress. Under an activated v2 changed lineage a governed mutation remains blocked unless its mapped gate exactly equals the current frontier.

#### Scenario: Scope or risk expands after approval
- **WHEN** the implementation adds a file family, behavior, permission boundary, non-goal exception, or risk trigger outside the authorized scope envelope
- **THEN** the old authorization MUST NOT permit implementation or later closeout actions
- **AND** the workflow MUST return to planning and direct-user confirmation
- **AND** a v1 cohort MUST use the later-v1 pre-change replacement path, while an activated v2 cohort MUST append the host-CAS event and replay every dependent gate before execution resumes

#### Scenario: Remote target drifts
- **WHEN** the remote URL fingerprint, target branch, or refreshed remote target tip differs from the authorized values
- **THEN** merge/push authorization MUST fail closed
- **AND** the workflow MUST NOT silently fetch-and-rebase, force push, rewrite history, or choose another target
- **AND** any later authorized target change MUST use its cohort's replacement path: later-v1 pre-change authority for v1, or a new event head/replay progress bound to the later authority epoch for activated v2

#### Scenario: New authority record lacks predecessor replay
- **WHEN** an activated-v2 later authority epoch mechanically covers the changed envelope but the requested action has open, missing, partial, or stale invalidated predecessors
- **THEN** that requested action MUST remain blocked at the current replay frontier
- **AND** authority consistency MUST NOT be represented as replay completion

#### Scenario: In-flight v1 stage needs replacement authority
- **WHEN** the introducing stage or any in-flight v1 stage has owner-authorized envelope or target drift before terminal
- **THEN** the existing v1 template/producer MUST remain available to create a later v1 epoch under the pre-change process
- **AND** the workflow MUST NOT require dormant v2 host CAS/replay or permit the caller to change cohorts

## ADDED Requirements

### Requirement: Authority and delivery v2 align archive-before-candidate ordering
Once a separate host-capability stage activates the v2 cohort, `stage_authority/v2` records SHALL use action order `plan -> implement -> archive -> commit -> merge -> push`, where `commit` means only the finite post-archive candidate. This introducing change leaves v2 dormant and completes under v1; existing and in-flight v1 records SHALL remain valid only under their pre-change schema/order until terminal and MUST NOT be reinterpreted. The existing `.harness/templates/stage-authority-record.template.json` and `.harness/templates/stage-delivery-binding.template.json` remain active v1 producers. Dormant v2 schemas use distinct `.harness/templates/stage-authority-record-v2.template.json` and `.harness/templates/stage-delivery-binding-v2.template.json` paths; callers cannot select them to change cohort. The v2 authority template MUST include the trigger-change binding. The v2 delivery binding MUST bind the exact current event/receipt counts/heads, authority, final review packet, and an exact pre-candidate object containing `expected_parent_oid`, `review_packet_sha256`, `reviewed_manifest_sha256`, `reviewed_inventory_sha256`, the fixed review-metadata/two-file-tail path set, and construction policy `single_parent_exact_subject_plus_metadata/v1`. It MUST NOT contain the future candidate OID or tree OID. After commit, the host retains the actual candidate OID externally and the candidate adapter validates its single parent and exhaustive subject-plus-metadata projection without rewriting the delivery binding.

#### Scenario: New v2 record is produced from its distinct repository template
- **WHEN** the dormant v2 authority template creates an initial or replacement authority record for an externally activated v2 cohort
- **THEN** template, strict schema, hash calculation, action order, trigger-change fields, validator, and tests MUST agree exactly

#### Scenario: Dormant v2 template is selected for a v1 stage
- **WHEN** a caller selects either v2 template for the introducing or an in-flight v1 stage
- **THEN** validation MUST fail before authority or delivery state changes
- **AND** the active v1 template/producer MUST remain unchanged and available through every v1 cohort's terminal state

#### Scenario: Delivery tail uses another replay state
- **WHEN** a delivery binding's event or receipt count/head differs from host-retained current replay state
- **THEN** candidate, merge, and push preflight MUST fail before mutation

#### Scenario: Delivery binding is complete before candidate creation
- **WHEN** the exact parent, final reviewed packet/manifest/inventory, fixed metadata/tail paths, authority and replay heads are known but no candidate commit exists yet
- **THEN** the v2 delivery binding MUST be fully constructible and mechanically valid
- **AND** neither a future candidate OID nor a future tree OID may be required

#### Scenario: Candidate is created from different inputs
- **WHEN** the live candidate has another parent, more than one parent, a subject or metadata path outside the bound exhaustive projection, or different authority/replay heads
- **THEN** candidate readiness MUST fail
- **AND** the delivery binding MUST NOT be rewritten after candidate creation to adopt that commit

#### Scenario: Introducing stage attempts to activate v2
- **WHEN** this replay implementation stage or another in-flight v1 stage reaches archive, candidate, merge, or push
- **THEN** the pre-change v1 process remains authoritative through terminal
- **AND** repository bytes MUST record v2 as `blocked_on_external_host_capability`, not as active
