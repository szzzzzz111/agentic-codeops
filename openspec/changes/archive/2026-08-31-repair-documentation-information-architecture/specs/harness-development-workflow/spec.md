## ADDED Requirements

### Requirement: Risk Routing Separates Semantic Change From Delivery Action

The workflow SHALL classify the semantic change before selecting review depth. Change class SHALL distinguish
read-only, mechanical, behavioral, and authority-sensitive work. File count MAY expand validation scope but MUST NOT,
by itself, raise semantic risk. The implementation review lane and later Git delivery action SHALL be recorded
separately; delivery preflight MUST NOT silently upgrade a low-risk semantic change into a medium/high review workflow.
The authority scope SHALL bind the required plan and implementation review slot counts for new zero-slot-capable
records. When an authority-bound low-risk contract requires zero independent review slots, the review validator SHALL
accept a schema-valid packet review set only when both receipts and review history are empty. A missing slot-count
binding, a caller count that differs from the bound count, or zero requested for a medium/high stage MUST fail closed.
Zero slots MUST NOT remove artifact-manifest, packet-hash, activation, authority, or exact receipt-count validation.
Non-integer or negative slot counts and non-empty receipts/history for a zero-slot contract MUST fail closed. Positive
slot counts MUST retain all existing reviewer independence and finding closure checks.

The binding MUST contain exactly `plan` and `implementation`, both non-negative integers excluding booleans. Each plan
or implementation review gate SHALL compare the caller count with the matching bound phase count for exact equality;
the other phase count MUST NOT substitute for it. Legacy records without the binding MAY retain positive-count
compatibility, but MUST NOT claim authority-bound review-count validation or request zero slots.
For a medium/high authority scope, both bound phase counts MUST be greater than zero. Authority-record shape validation
MUST fail when either phase is zero, regardless of which phase the current action consumes.

For an authority record containing the binding, the `implement` preflight SHALL consume the canonical plan review set at
`.harness/reviews/<stage-id>/plan/review-set.json`, the caller's plan slot count, and the host-retained expected plan packet
hash. It SHALL validate the set with `expected_phase=plan` and reject missing or non-canonical inputs, wrong phase or packet,
incomplete manifest/activation/authority evidence, implementation-set substitution, and any mismatch with the bound plan
count. The current introducing stage's epoch-5 plan MAY remain governed by its pre-change process and MUST NOT be reported as
retroactively validated by the new gate. A zero-slot result SHALL mark reviewer dispatch provenance not applicable while
retaining activation chronology and authority binding as required external evidence.
The expected plan packet hash SHALL be a host-retained hash of the exact canonical artifact manifest; removing or replacing
an artifact MUST change the computed packet hash and fail against the unchanged host value. Repository validation SHALL NOT
claim that a caller-selected replacement is host authority. The zero-history rule applies to the submitted current review
set; cross-version prior-set discovery or append-only history requires external host CAS and is not claimed by this v1 gate.

#### Scenario: Broad mechanical documentation update remains low risk

- **WHEN** a stage changes only durable documentation and deterministic documentation checks without changing runtime behavior
- **THEN** internal review and relevant structural validation SHALL be sufficient unless an escalation trigger is observed
- **AND** a later authorized Git action SHALL use its own delivery preflight without retroactively adding semantic review slots

#### Scenario: Zero-slot delivery keeps packet binding

- **WHEN** a low-risk authority scope binds zero independent review slots and the review set has empty receipts/history
- **THEN** the validator accepts the zero count only after the packet manifest, hashes, activation, and exact receipt count pass
- **AND** archive or commit remains blocked when any required packet or authority evidence is missing

#### Scenario: Zero-slot contract contains a manufactured receipt

- **WHEN** `required_slots=0` but the review set contains one or more receipts
- **THEN** validation fails closed with an exact-count mismatch

#### Scenario: Zero-slot contract carries unresolved review history

- **WHEN** `required_slots=0` but review history is non-empty
- **THEN** validation fails closed before any historical finding can be hidden from current receipts

#### Scenario: High-risk caller requests zero slots

- **WHEN** a medium/high authority or an authority without a zero-slot binding supplies `required_slots=0`
- **THEN** stage-authority validation fails closed even when the packet manifest and empty review set are otherwise valid

#### Scenario: High-risk record hides zero plan slots behind positive implementation slots

- **WHEN** a medium/high authority binds `plan=0` and `implementation=2` while the current action consumes implementation
- **THEN** authority-record shape validation fails before the positive implementation count can hide the zero plan binding

#### Scenario: High-risk record hides zero implementation slots behind positive plan slots

- **WHEN** a medium/high authority binds `plan=2` and `implementation=0` while the current action consumes plan
- **THEN** authority-record shape validation fails before the positive plan count can hide the zero implementation binding

#### Scenario: Bound positive count is downgraded

- **WHEN** authority binds two slots for the current phase but the caller supplies one or three
- **THEN** stage-authority validation fails before the receipt count can be accepted

#### Scenario: Caller substitutes the other phase count

- **WHEN** plan and implementation counts differ and the caller supplies the count bound to the other phase
- **THEN** validation fails against the exact current phase binding

#### Scenario: Bound future stage enters implementation

- **WHEN** a future authority record binds a plan slot count and requests the `implement` action
- **THEN** the gate consumes the canonical plan review set with the host-retained packet hash and `expected_phase=plan`
- **AND** missing, substituted, non-canonical, wrong-phase, wrong-packet, or incomplete evidence fails closed

#### Scenario: Introducing stage cannot retroactively validate its own plan

- **WHEN** the validator change is being introduced under the current stage's epoch-5 pre-change plan process
- **THEN** that plan is not reported as having passed the new authority-bound implement gate
- **AND** the exception does not apply to later authority records containing the slot-count binding

#### Scenario: Review slot binding schema is malformed

- **WHEN** the binding is missing a phase, has an extra field, or contains a boolean, float, string, or negative value
- **THEN** the authority record fails closed as schema-invalid

#### Scenario: Slot count is not a non-negative integer

- **WHEN** the requested independent review slot count is negative, boolean, floating-point, string, or otherwise not an integer
- **THEN** validation fails closed before any review receipt can contribute to readiness

#### Scenario: A low-risk stage discovers behavioral impact

- **WHEN** implementation requires public/runtime behavior, permission, persistence, network, Git/subprocess semantics,
  test weakening, or an unsafe automated fix
- **THEN** the stage SHALL stop and reclassify upward before making that change

### Requirement: Tracked Handoff Is A Stable Resume Protocol

`HANDOFF_TO_NEXT_CHAT.md` SHALL contain stable resume commands, reading order, safety boundaries, and rules for querying
live state. It MUST NOT claim the branch, HEAD, worktree, candidate, merge, push, remote parity, or active-change state
of the commit that contains it. Those facts SHALL come from live Git/OpenSpec commands and controller output.

#### Scenario: Volatile assignments use common bilingual Markdown forms

- **WHEN** a tracked handoff assigns a current branch, HEAD, worktree, candidate, merge, push, remote parity, or
  active-change value through a Chinese or English label, with or without `当前`/`current`, using `:` or `：`, and the
  label MAY be wrapped by Markdown list, emphasis, or inline-code syntax
- **THEN** the deterministic documentation scanner SHALL fail closed after normalizing those wrappers

#### Scenario: Stable live-query guidance does not assign tracked state

- **WHEN** Chinese or English handoff guidance says that volatile facts are queried live through Git, OpenSpec, or
  controller commands without assigning their current values
- **THEN** the deterministic documentation scanner SHALL accept that guidance

#### Scenario: Delivery completes after the documentation candidate is frozen

- **WHEN** merge or push occurs after the tracked documentation packet is committed
- **THEN** the tracked handoff SHALL remain correct without a follow-up self-referential docs commit
- **AND** the final user handoff SHALL report live delivery state outside the tracked file

### Requirement: Current Architecture And Indexes Are Structurally Checkable

`docs/ARCHITECTURE.md` SHALL present current runtime relationships and a component-to-code map before historical links.
Its current surface MUST NOT use second-level version-by-version architecture headings. A migration appendix MAY retain
legacy prose only when it is collapsed, explicitly non-canonical, and points to archived OpenSpec as the history owner.
`openspec/specs/README.md` SHALL index every current capability directory. Deterministic docs checks SHALL fail when
these structural contracts or acceptance-only FEATURE_LIST boundaries drift.

#### Scenario: A capability directory is added without updating the index

- **WHEN** a direct child of `openspec/specs/` contains `spec.md` but is absent from the specs index
- **THEN** the documentation scan SHALL fail with the missing capability name

#### Scenario: Acceptance inventory contains stage narration

- **WHEN** a FEATURE_LIST note describes cleanup or delivery as active, pending, future, or current-stage work
- **THEN** the documentation scan SHALL fail instead of treating the inventory as acceptance-only
