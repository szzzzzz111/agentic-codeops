## MODIFIED Requirements

### Requirement: Plan Review Gates Precede Implementation

Medium and high risk RepoPilot stages SHALL complete plan-level review before runtime or test implementation begins.

Plan-level review MUST include internal plan review, two independently instantiated plan-review slots, and triage of all findings. Passing OpenSpec validation MUST NOT be treated as plan review. Reviewer provider or product identity MUST NOT be the sole reason a review slot passes or fails.

Each first-round independent reviewer MUST be distinct from the implementer and the other independent reviewer, MUST review the same frozen plan baseline, MUST NOT inherit the implementation conversation, and MUST NOT read the other first-round review conclusion before producing its own conclusion. A Codex reviewer MAY satisfy either independent slot through a new empty-context task or a subagent invocation that explicitly disables parent-context inheritance. A Codex task/subagent with inherited implementation context or unverified context mode MUST NOT satisfy an independent review slot.

Each independent review record MUST identify stage/phase/slot id, implementer instance identity, reviewer provider/model/instance identity, host-reported context inheritance mode, an immutable reviewed Git/tree or packet-manifest ref and artifact hashes, whether other first-round conclusions were visible, final findings or an explicit no-findings conclusion, finding disposition/closure, remediation lineage when applicable, and residual uncertainty. Remediation lineage MUST resolve a content-hashed original first-round receipt and MUST bind the original slot, reviewer, and finding IDs. Different providers or models MAY add diversity evidence, but MUST NOT replace the context and instance independence requirements. A deterministic validator MUST reject mechanically observable identity collisions, duplicate slots/reviewers, declared inherited or unknown context, declared first-round cross-review visibility, noncanonical/mutable/mismatched baselines, missing artifact hashes, stale post-remediation receipts, unresolved lineage, contradictory or open final conclusions, and incomplete records.

Actual review sets MUST be stored at `.harness/reviews/<stage-id>/<phase>/review-set.json` and validated with `scripts/validate_independent_review.py` against explicit expected stage, phase, and required-slot count. The validator MUST recompute reviewed artifact hashes and the content-addressed packet hash from canonical project-relative files, emit structured errors, and exit nonzero on any mechanical defect. It MUST label its claim `mechanical_consistency_only`, MUST NOT claim that repository-authored fields prove host dispatch provenance or activation chronology, and MUST leave `gate_ready=false`. The host controller MUST separately verify native reviewer/implementer dispatch identity, parent-context inheritance and first-round visibility, while the pre-change process authority MUST verify activation sequence. A receipt set that is missing, was not passed to the validator, returned nonzero, or lacks either required external check MUST NOT contribute any completed review slot.

When a stage introduces this validator or another new review gate, activation timing MUST remain owned by the pre-change process authority and MUST occur only after implementation, negative tests, and workflow wiring pass. The receipt MUST bind a project-relative activation record and its hash; the validator MAY verify record integrity but MUST NOT claim to prove chronology. The introducing stage's earlier plan review MUST remain governed by the pre-change review contract and frozen review evidence; the workflow MUST NOT retroactively claim that the not-yet-created validator ran before implementation. Once activated, the new gate MUST govern the introducing stage's final implementation review and all subsequent applicable plan/final independent reviews.

#### Scenario: Implementation waits for two independent plan reviews

- **WHEN** a medium or high risk stage reaches the implementation confirmation gate
- **THEN** internal plan review MUST check proposal, design, tasks, spec deltas, test plan, and Harness boundaries
- **AND** two distinct independent reviewer instances MUST each return severity findings or an explicit no-findings conclusion against the same frozen baseline
- **AND** all plan findings MUST be classified as `fix`, `clarify`, `reject`, or `defer`

#### Scenario: Codex replaces an OpenCode review slot

- **WHEN** a required independent plan-review slot is assigned to Codex instead of OpenCode
- **THEN** the reviewer MUST use a new empty-context task or a subagent with parent-context inheritance explicitly disabled
- **AND** inherited or unverified context MUST keep the independent review gate open

#### Scenario: First-round reviewers remain blind to each other

- **WHEN** two independent reviewers inspect the first frozen plan baseline
- **THEN** neither reviewer MUST receive the other reviewer's findings before producing its own first-round conclusion
- **AND** repeating another reviewer's conclusion MUST NOT count as independent counterexample evidence

#### Scenario: Re-review preserves finding lineage

- **WHEN** implementation or plan artifacts change to remediate an existing finding
- **THEN** the original reviewer session MAY be reused to verify closure of that finding
- **AND** the reused session MUST continue to occupy only its original review slot and MUST NOT be counted as an additional independent reviewer
- **AND** remediation lineage MUST resolve a content-hashed original first-round receipt with the same slot/reviewer and the referenced finding IDs
- **AND** every required slot MUST issue a final receipt against the same final content-addressed baseline before the gate closes

#### Scenario: OpenCode adapter timeout is not a verdict

- **WHEN** an OpenCode adapter command times out or does not print a final result
- **THEN** the agent MUST inspect the relevant OpenCode session for final assistant review text before marking that adapter attempt failed
- **AND** missing final review text keeps that slot open until the same attempt is recovered or another independently instantiated reviewer satisfies it; adapter unavailability MUST NOT reduce the required slot count

#### Scenario: OpenCode first-round review uses an isolated session

- **WHEN** OpenCode is assigned a first-round independent review slot
- **THEN** it MUST use a new isolated review session or provide host evidence that a candidate session contains no implementation conversation or other first-round conclusion
- **AND** ordinary session reuse MUST be limited to timeout recovery of the same attempt or remediation re-review for the same slot

#### Scenario: Review evidence proves independence

- **WHEN** an independent plan review is recorded as complete
- **THEN** its validated receipt MUST identify implementer and reviewer identities, slot, host-reported context mode, immutable frozen ref and artifact hashes, conclusion visibility, final conclusion, lineage, and residual uncertainty
- **AND** repository validation MUST remain mechanical-only while the host controller separately verifies native dispatch provenance
- **AND** provider/model diversity without context isolation MUST NOT satisfy the gate

#### Scenario: Review gate consumes the actual receipt set

- **WHEN** a workflow attempts to count required independent review slots
- **THEN** it MUST run the independent-review validator against the actual stage/phase receipt set with the risk-contract required-slot count
- **AND** missing invocation, missing receipts, stale packet hashes, nonzero validation, missing host dispatch verification, or missing activation-sequence verification MUST keep the review gate open

#### Scenario: Newly introduced review gate does not self-bootstrap

- **WHEN** a process change implements a new independent-review validator or gate
- **THEN** the change's pre-implementation plan review MUST use and preserve the pre-change review contract and frozen evidence
- **AND** the pre-change process authority MUST own and record activation only after implementation and negative verification, beginning with that change's final review and subsequent applicable reviews
- **AND** the repository validator MUST NOT claim that a declarative activation field proves that chronology
- **AND** later validation MUST NOT be reported as if it preceded implementation

### Requirement: External Review Seeks Independent Counterexamples

独立 review SHALL target failure modes not already covered by task completion reporting. Findings SHOULD include severity, location, trigger, consequence, and a suggested regression test. External feedback MUST be classified as `fix`, `clarify`, `reject`, or `defer` against repository evidence.

The same reviewer-slot independence contract SHALL apply to every independent slot required by plan review or final implementation review. Medium/high plan review retains two independent slots; final implementation review slot count remains defined by the stage risk contract. A first-round reviewer MUST inspect a frozen review packet without inherited implementation conversation or another first-round reviewer conclusion. A remediation re-review MAY reuse the original reviewer session to preserve finding lineage, but that reused session MUST NOT create an additional independent slot. After remediation, every required slot's final receipt MUST bind the same final content-addressed baseline.

Code review SHALL assess layered concerns: scope, business logic, architecture boundaries, minimality, failure semantics, security/privacy, test adequacy, and maintainability. The agent SHALL own low-level implementation review by default and translate findings into user-facing Chinese summaries when the user needs to judge product behavior, workflow semantics, risk acceptance, or residual risk.

#### Scenario: External review repeats implementation status

- **WHEN** independent feedback only repeats tasks, passing tests, implementation status, or another first-round review conclusion without an independent failure hypothesis
- **THEN** it MUST NOT be treated as meaningful diversity evidence

#### Scenario: Final implementation reviewer uses an isolated instance

- **WHEN** a stage requires independent final implementation review
- **THEN** every required first-round reviewer slot MUST use a distinct instance with no inherited implementation conversation and review the same frozen final code/test packet
- **AND** a Codex empty-context task or parent-context-disabled subagent MAY satisfy any required slot regardless of whether OpenCode is available
- **AND** remediation MUST refresh every required slot's final receipt to the same final baseline before the final review gate closes

#### Scenario: User-facing review summary explains terms

- **WHEN** review results include non-obvious engineering terms
- **THEN** the summary keeps the precise term and adds a short Chinese explanation or concrete example

#### Scenario: Independent reviewer reports findings

- **WHEN** an independent reviewer reports plan or implementation findings
- **THEN** each finding MUST be classified as `fix`, `clarify`, `reject`, or `defer`
- **AND** accepted fixes or clarifications MUST be reflected in the reviewed artifacts before the relevant gate closes
