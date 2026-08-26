## ADDED Requirements

### Requirement: Material stage changes use an append-only host-bound event lineage
An activation that enables blocking replay MUST record every material post-baseline change to an already closed or bound stage input in one canonical append-only event lineage. The host SHALL retain a monotonic gate-lifecycle/input snapshot plus prior event and receipt count/head values. Every append MUST prove by compare-and-swap that each prior retained head remains the exact unmodified prefix and only the allowed contiguous entry was added before the host atomically adopts the proposed next state. Ordinary edits while their initial gate is mechanically open, and exact code-owned archive/candidate/merge/push transition outputs, MAY use the no-event path only when the live pre-state, exact delta, and post-state match the host snapshot and transition adapter. Every event SHALL bind the stage id, sequence, predecessor hash, host-issued event identity, event kind, bounded source reference, authority-before epoch/hash, authority requirement, declared changed facts, before/observed input snapshot digests, and a canonical payload digest. Repository bytes alone MUST NOT prove that no event was omitted or that a source reference is authentic.

Repository validators SHALL accept a versioned `controller_stage_context/v1` only to report `mechanical_consistency_only`; they cannot prove the context's provenance. Blocking activation requires an external `provider_neutral.stage_state_cas/v1` implementation with host-owned `load`, atomic `compare_and_swap`, restart-safe `recover`, atomic `close`, and non-repository reviewer-dispatch metadata. The state key and context MUST bind a host-issued workspace id, the raw-byte digest of the host's initial canonical project root, Git common-dir identity, worktree git-dir identity, stage id, and planning base. Repository files, CLI flags, handoff text, receipts, activation hashes, or a mechanically passing fixture MUST NOT satisfy that capability. Until a separately reviewed and authorized host implementation supplies positive restart/CAS/dispatch evidence, supported entrypoints SHALL keep the pre-change gate active and SHALL NOT use replay PASS to authorize mutation.

#### Scenario: No material change has occurred
- **WHEN** the host passes prior/current event and receipt counts `0` with all heads `none`, the canonical stage replay directory is absent or exactly empty, and every closed/bound gate live input equals the host-retained lifecycle snapshot
- **THEN** the validator MAY report the no-change state mechanically consistent
- **AND** omission or mismatch of any lineage/snapshot input MUST fail rather than default to no change

#### Scenario: Closed input changes while caller still claims no event
- **WHEN** implementation, verification, review, authority, or delivery input differs from a host-retained closed/bound gate snapshot while event count/head remain `0/none`
- **THEN** preflight MUST return `MATERIAL_CHANGE_EVENT_REQUIRED`
- **AND** a regenerated local PASS artifact MUST NOT erase the missing event

#### Scenario: Host state capability is unavailable
- **WHEN** an entrypoint is asked to activate blocking replay but cannot recover prior gate snapshots, lineage CAS state, terminal state, immutable workspace binding, or required dispatch provenance from `provider_neutral.stage_state_cas/v1`
- **THEN** the replay activation path MUST fail before repository mutation with `HOST_STATE_UNAVAILABLE`
- **AND** the already active pre-change workflow remains authoritative; a shadow/mechanical PASS MUST NOT be treated as activation or mutation authority

#### Scenario: Caller selects an alternate workspace or replay directory
- **WHEN** the supplied project/replay root is a sibling clone, another linked worktree, symlink alias, snapshot, parent, or any identity other than the host-bound initial workspace and `.harness/change-replay/<expected-stage>` within it
- **THEN** validation MUST return a structured failure before consuming event or receipt bytes
- **AND** a caller-selected root that is internally canonical MUST NOT replace the host-issued workspace binding

#### Scenario: Repository omits a host-observed event
- **WHEN** the host-retained event count or head differs from the repository lineage
- **THEN** validation MUST fail before implementation or closeout continues
- **AND** an internally consistent older lineage MUST NOT satisfy the current change gate

#### Scenario: Event lineage forks or skips a predecessor
- **WHEN** sequence numbers are non-contiguous, a predecessor hash is wrong, two candidate heads exist, or a prior event is deleted
- **THEN** validation MUST return a structured redacted failure
- **AND** no replay progress may inherit evidence from that lineage

#### Scenario: Prefix is rewritten before a new append
- **WHEN** a candidate lineage reaches a new internally consistent head but the host-retained prior head is not its exact byte-for-byte prefix
- **THEN** append validation MUST fail before host state is updated
- **AND** ordinary action preflight MUST NOT adopt the candidate head

### Requirement: Event kinds enforce distinct authority ceilings
The workflow SHALL distinguish `direct_user_envelope_change`, `agent_technical_correction`, `review_remediation`, and `repository_or_git_drift`. A direct-user envelope change MUST bind a later authority epoch and a new host-observed direct-user decision. Agent technical correction and review remediation MUST remain inside the current authority envelope and MUST NOT expand scope, non-goals, risk, action ceiling, endpoint, branch, or authorized tip. A review-remediation event MUST declare `review_phase=plan|implementation`; plan-phase remediation MAY include `plan_subject`, while implementation-phase remediation MAY include only implementation/workflow/template/verification/review-binding facts. Both phases MUST bind the original slot, receipt, finding ids, and affected evidence. Repository/Git drift MUST fail closed and MUST NOT trigger automatic rebase, history rewrite, target substitution, or authority inheritance.

The V1 validator MUST recognize only the exact changed-fact identifiers and kind/fact combinations defined by the code-owned mapping in the reviewed design. Unknown identifiers, duplicate identifiers, or a fact outside its event-kind ceiling MUST return a structured failure. A repository/Git drift event reports observed drift only and MUST NOT convert the observed value into an authorized value.

#### Scenario: Technical correction stays inside the envelope
- **WHEN** an Agent changes implementation or test strategy without changing the authorized scope, non-goals, risk, action ceiling, or Git target
- **THEN** the event MAY retain the current authority epoch
- **AND** it MUST still invalidate every affected verification, review, and downstream delivery gate

#### Scenario: Agent event attempts to expand scope
- **WHEN** an `agent_technical_correction` or `review_remediation` declares or causes an envelope expansion
- **THEN** validation MUST fail with a structured classification/authority error
- **AND** the workflow MUST require a direct-user envelope change and later authority epoch

#### Scenario: Event uses an unknown or wrong-kind changed fact
- **WHEN** an event contains an unknown changed-fact id, a duplicate id, or a fact outside the code-owned ceiling for its event kind
- **THEN** validation MUST fail before invalidation or preservation is computed

#### Scenario: Review remediation lacks finding lineage
- **WHEN** a review remediation event does not reference the original review slot, receipt, finding ids, and affected evidence
- **THEN** the event MUST NOT close replay

#### Scenario: Plan review finding changes the plan subject
- **WHEN** a plan reviewer finding is remediated without expanding owner-bound facts
- **THEN** `review_remediation` with `review_phase=plan` MUST bind the original same-slot lineage and seed replay at `plan_contract`
- **AND** using a generic technical event to omit finding lineage MUST fail

### Requirement: Invalidation is recomputed from a versioned gate dependency graph
The V1 validator SHALL use the code-owned linear graph `plan_contract -> plan_review -> authority -> implementation -> verification -> implementation_review -> archive -> post_archive_delivery_review -> candidate -> merge -> push`. Each exact changed-fact id SHALL map to one reviewed earliest seed. The exact invalidated and required-replay sets are the complete suffix beginning at the earliest seed; the preserved set is the complete prefix before that seed only when every host snapshot/input binding remains unchanged. A repository receipt MUST NOT supply or weaken the graph. The replay frontier SHALL be the earliest uncompleted node in that suffix, represented as a set. A fixed numeric resume step, special target/review skip edge, or self-declared later resume point MUST NOT be accepted.

#### Scenario: Scope or product contract changes
- **WHEN** scope, non-goals, risk, requirements, public behavior contract, or planned file families change
- **THEN** plan contract, applicable plan review, authority, implementation, verification, implementation review, and all downstream closeout gates MUST be invalidated according to the graph

#### Scenario: Review subject changes inside the same envelope
- **WHEN** implementation bytes change after verification or implementation review while the authority envelope remains unchanged
- **THEN** the authority gate MAY be preserved
- **AND** affected verification, implementation review, archive, delivery review, candidate, merge, and push gates MUST be replayed

#### Scenario: Target-only drift uses the conservative V1 suffix
- **WHEN** endpoint, target branch, authorized remote tip, action ceiling, or authority record changes
- **THEN** `authority` and its entire downstream suffix MUST be invalidated in V1
- **AND** implementation evidence MUST NOT be specially preserved by an undocumented direct-input edge

#### Scenario: V1 computes a set-valued frontier
- **WHEN** one event declares one or more changed facts under the V1 linear gate graph
- **THEN** `replay_frontier_gate_ids` MUST equal the exact set of earliest invalidated nodes derived from the code-owned mapping
- **AND** the validator MUST NOT accept a numeric resume step or a receipt-declared later gate

#### Scenario: A later graph version introduces parallel nodes
- **WHEN** a future reviewed graph version contains multiple invalidated branches with no ordering edge between their earliest gates
- **THEN** `replay_frontier_gate_ids` MUST preserve every earliest node
- **AND** the graph version and corresponding negative tests MUST change together

#### Scenario: Receipt omits one derived invalidation
- **WHEN** declared invalidated, preserved, replay, or frontier sets differ from the validator's recomputed exact sets
- **THEN** validation MUST fail even if every listed receipt hash is internally consistent

#### Scenario: Every fact id has one exact-set fixture
- **WHEN** the V1 mapping or graph version changes
- **THEN** parameterized tests MUST assert the full invalidated, preserved, required-replay, and initial-frontier sets for every fact id

### Requirement: Preserved evidence proves unchanged inputs and dependency closure
A gate MAY remain preserved only when every direct input binding is unchanged, every dependency gate is preserved or freshly closed, every referenced current artifact hash still matches a canonical non-symlink project file or exact Git/ref fact, and no newer event exists. A boolean, timestamp, chat summary, or repository-authored conclusion MUST NOT establish preservation.

#### Scenario: Evidence file hash remains the same but its dependency changed
- **WHEN** an evidence file's bytes are unchanged but an upstream requirement, authority, artifact, command contract, or review packet input changed
- **THEN** the evidence MUST be invalidated
- **AND** byte equality alone MUST NOT preserve the consumer gate

#### Scenario: Unaffected evidence has complete binding proof
- **WHEN** a gate's direct inputs, dependency closure, artifact hashes, Git facts, and event head are all unchanged
- **THEN** the gate MAY be retained without replay
- **AND** the validation report MUST identify the exact preservation basis

#### Scenario: Preserved artifact path is unsafe or missing
- **WHEN** an evidence ref escapes the project, traverses a symlink, is not a regular file, is missing, or differs from its declared hash
- **THEN** validation MUST return a structured redacted failure without traceback

### Requirement: Completed gates use code-owned evidence adapters
The validator MUST accept gate completion only from the reviewed adapter assigned to that gate and graph version. The V1 adapters SHALL cover exact OpenSpec plan contract/strict validation, actual independent plan review plus external host dispatch and activation checks, authority-core validation before replay, exhaustive implementation subject inventory, an allowlisted verification bundle with exact command ids/argv/cwd/required set/input generation, actual independent implementation review plus external checks, exact OpenSpec archive mapping/post-archive validation, final delivery review, exact candidate, ff-only merge, and exact-lease push/reconciliation. Unknown producer/schema, arbitrary hashed files, free-form command digests, partial command sets, repository-authored PASS conclusions, or mechanical review PASS without required host facts MUST NOT complete a gate.

#### Scenario: Arbitrary current file claims verification PASS
- **WHEN** a replay receipt points `verification` at a current hash-matching file that is not a valid `verification_bundle/v1` from the code-owned producer and exact subject generation
- **THEN** verification MUST remain incomplete
- **AND** later mutation readiness MUST remain blocked at the verification frontier

#### Scenario: Mechanical review PASS lacks host dispatch evidence
- **WHEN** `validate_independent_review` mechanically passes but the host has not verified native dispatch provenance or activation sequence
- **THEN** plan/implementation review MUST NOT be counted completed for action readiness

#### Scenario: Authority core and replay are evaluated without recursion
- **WHEN** stage authority evaluates a requested action
- **THEN** it MUST validate the authority record/envelope core first and pass a bounded core-result digest into replay validation
- **AND** replay validation MUST NOT consume the outer authority report that itself depends on replay

### Requirement: Replay progress is current-head exact and monotonic
Each replay receipt SHALL bind exactly one event head, its predecessor receipt hash, the host snapshot generation, and the current authority epoch/hash, and MUST contain valid adapter evidence for every gate it declares completed. Completed replay gates may only grow monotonically for one event head and MUST respect graph order. Receipt append MUST compare the host-retained prior count/head with the unchanged local prefix before returning a proposed next state; ordinary action validation requires exact equality to the already retained current head. A later event MUST make every earlier replay progress record stale. Final review-set, delivery binding, candidate, merge, and push facts MAY be consumed as existing tail/host/live inputs but MUST NOT be copied back into a pre-frozen replay receipt or create another evidence-tail file.

#### Scenario: Older replay receipts are deleted or rewritten
- **WHEN** the local receipt lineage is internally consistent but the host-retained prior count/head is not its exact unchanged prefix
- **THEN** validation MUST fail
- **AND** the rewritten lineage MUST NOT be called append-only

#### Scenario: Requested action is later than the current frontier
- **WHEN** any invalidated predecessor of the requested action lacks fresh current-input evidence or remains open
- **THEN** `requested_action_ready` MUST be false and the report MUST identify the current frontier
- **AND** the requested mutation MUST report `STAGE_REPLAY_REQUIRED`

#### Scenario: Requested action is the current frontier
- **WHEN** every invalidated predecessor is freshly closed, preserved inputs remain exact, and the requested action is the earliest open invalidated gate
- **THEN** `requested_action_ready` MAY be true
- **AND** downstream merge or push gates MUST NOT be required to appear completed before their own execution

#### Scenario: Requested mutation is earlier than the frontier
- **WHEN** the frontier is `verification` or later and a caller requests `implement`, or any governed mutation maps to a preserved earlier gate
- **THEN** preflight MUST fail with `ACTION_BEHIND_REPLAY_FRONTIER`
- **AND** returning to that mutation requires a new host-CAS accepted material-change event

#### Scenario: New event appears after replay progress
- **WHEN** a later event is appended after an earlier replay receipt recorded progress
- **THEN** the earlier progress MUST become stale automatically
- **AND** the new event's invalidation and replay MUST be recomputed from the new head

#### Scenario: Tail and live evidence close later predecessors without receipt recursion
- **WHEN** a later action requires implementation review, delivery binding, candidate, merge, or push evidence that is carried by the existing two-file tail or host/live Git state
- **THEN** validation MAY compose that exact evidence into requested-action readiness
- **AND** it MUST NOT rewrite the replay receipt, add a third tail file, or imply live human authority, semantic correctness, or Git delivery success

### Requirement: Replay state is consumed before governed actions after activation
For a stage in the explicitly activated v2 cohort, every governed implement, archive, commit, merge, and push preflight SHALL require explicit host-retained lineage/snapshot/terminal/workspace inputs and the canonical replay state. Under a changed lineage the mapped gate MUST equal the exact current frontier; both earlier and later mutation actions fail before mutation. Under no-change, the host snapshot plus code-owned normal transition state machine MUST prove sequence readiness; an empty invalidated set alone grants nothing. A dormant validator or shadow report MUST NOT alter action readiness for a v1 cohort.

For `stage_authority/v2`, the action order MUST be `plan -> implement -> archive -> commit -> merge -> push`, and the code-owned mapping is `implement -> implementation`, `archive -> archive`, `commit -> candidate`, `merge -> merge`, and `push -> push`. `commit` means only the finite post-archive candidate. Existing v1 records retain legacy ordering and MUST NOT be reinterpreted as v2. Unknown actions or alternate mappings fail. Plan/authority, read-only verification, and independent review use their adapters. Event/receipt projection writes are controller-only CAS evidence transitions restricted to the canonical stage replay directory; they MUST NOT mutate implementation subjects or elevate the action ceiling and MUST enter the final reviewed subject.

#### Scenario: Apply entrypoint omits change inputs
- **WHEN** a supported Codex/OpenCode implementation entrypoint invokes the authority gate without explicit expected change count and head
- **THEN** the preflight MUST fail before implementation files change

#### Scenario: Closeout uses stale replay progress
- **WHEN** archive, merge, or push receives replay progress or external gate evidence for another event head, authority epoch, review packet, candidate, or Git target
- **THEN** preflight MUST fail before mutation

#### Scenario: Legacy commit ceiling is not reinterpreted
- **WHEN** a v1 authority record uses the legacy `commit` ceiling
- **THEN** the validator MUST apply only v1 semantics and MUST NOT treat it as authority for a v2 post-archive candidate
- **AND** new v2 template records MUST use the v2 archive-before-commit ordering

#### Scenario: Introducing or in-flight v1 stage reaches closeout
- **WHEN** the replay implementation stage or any stage already in flight before later host activation has a v1 authority record
- **THEN** it MUST complete under the pre-change v1 workflow through terminal without replay enforcement or v2 reinterpretation
- **AND** only stages newly created after a separately reviewed host-capability activation MAY enter the v2 cohort

#### Scenario: Activation is inferred from repository bytes
- **WHEN** a caller presents a repository activation record, schema version, date, hash, CLI boolean, or mechanically passing fixture without the exact external host activation chronology and capability evidence
- **THEN** blocking replay MUST remain inactive
- **AND** the workflow MUST NOT infer a v2 cohort

### Requirement: Verified push creates an external terminal stage tombstone
For an explicitly host-activated v2 stage, after same-endpoint reconciliation verifies the exact candidate on the exact target branch, the host MUST atomically retain a terminal tombstone binding immutable workspace identity, stage id, candidate, endpoint fingerprint, branch, verified remote tip, and `status=closed`. Every later same-stage event append or governed action MUST fail with `NEW_STAGE_REQUIRED`. An unknown push outcome MUST retain `delivery_unknown` and allow only same-endpoint reconciliation, not ordinary replay append. The tombstone MUST remain external because post-push repository writes would invalidate the delivered candidate. A dormant repository fixture does not establish this terminal capability.

#### Scenario: Closed stage is reused after controller restart
- **WHEN** the host restores a verified-push terminal tombstone and a caller submits a new event or apply request for the same stage id
- **THEN** the request MUST fail with `NEW_STAGE_REQUIRED`
- **AND** a new stage id, planning base, and authority envelope are required

#### Scenario: Unknown push outcome is not closed
- **WHEN** push outcome is `unknown`
- **THEN** the stage MUST NOT be marked closed
- **AND** only same-endpoint read-only reconciliation is allowed until the outcome is resolved

### Requirement: Change replay remains a development-only capability
Stage change events, invalidation receipts, replay validators, skills, and workflow commands SHALL remain repository development-process assets. They MUST NOT add RepoPilot runtime event ingestion, background execution, runtime subagents, automatic patching, automatic commit/merge/push, credential handling, or public API behavior.

#### Scenario: Replay assets are installed
- **WHEN** the repository contains the new templates, scripts, receipts, or workflow wiring
- **THEN** `app/**`, `/chat`, runtime capability reporting, persistence schemas, provider behavior, and network defaults MUST remain unchanged
