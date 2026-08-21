## MODIFIED Requirements

### Requirement: Continuous Authorization Does Not Remove Formal Review

用户对实现、提交、归档、合并或推送的连续执行授权 SHALL reduce only intermediate stage-level
confirmation prompts. It MUST NOT remove or weaken formal code review, Stage Debt Sweep, deterministic
validation, archive review, merge review, or post-merge verification.

Continuous authorization MUST bind an exact stage id, current authority epoch/record hash, risk, scope envelope,
planning baseline, action ceiling, effective fetch/push endpoint fingerprints, target branch, and authorized remote
tip. Scope, risk, baseline, action ceiling, endpoint, branch, or refreshed target-tip drift MUST invalidate inherited authorization for the affected action. Repository
records and validators MUST remain mechanical-only evidence; the host controller MUST separately verify the live
direct-user authority.

The shared gate MUST accept authority only from the canonical resolved
`<project-root>/.harness/authority/<expected-stage>` directory. It MUST preserve Git `-z` path fields as raw bytes
until strict reversible canonical representation succeeds, and malformed `allowed_path_rules` MUST produce a
structured redacted failure without traceback. Before `ls-remote`, credential-helper invocation, or any remote/network
contact, the workflow MUST locally prove that effective fetch/push endpoints are each unique, are equal, and that both
fingerprints match the host-retained expected values.

Formal code review MUST run after the final runtime/test changes and before archive/merge, and MUST produce a
visible severity-ordered findings report or an explicit no-findings conclusion with residual risks. Passing tests,
incremental self-checks, checked task/checklist items, review receipts, or authority hashes MUST NOT be treated as
equivalent evidence.

#### Scenario: Merge authorization preserves review gates

- **WHEN** the user authorizes execution through merge or push
- **THEN** the agent still performs and reports formal code review before archive/merge
- **AND** unresolved P0/P1 findings block archive/merge or reopen closeout if discovered afterward

#### Scenario: Continuous authorization stays inside the exact envelope

- **WHEN** the user authorizes execution through a named action and all bound stage, risk, scope, baseline, remote, branch, and target-tip facts remain unchanged
- **THEN** the workflow MAY continue without repeating intermediate stage-level confirmation prompts
- **AND** every technical, review, archive, and Git preflight gate still applies

#### Scenario: Material stage or Git target drift invalidates authorization

- **WHEN** scope, risk, action ceiling, planning baseline identity, remote fingerprint, target branch, or refreshed remote tip changes
- **THEN** the old authorization MUST stop the affected action
- **AND** a new direct-user decision and later authority epoch are required

#### Scenario: Endpoint mismatch stops before remote contact

- **WHEN** fetch/push endpoint equality is unproven or either locally resolved fingerprint differs from its host-retained expected value
- **THEN** the workflow MUST stop before `ls-remote`, credential-helper invocation, or any network contact
- **AND** it MUST NOT contact the mismatched endpoint to determine whether it is usable

#### Scenario: Authority directory is substituted

- **WHEN** the supplied authority directory does not canonical-resolve exactly to `<project-root>/.harness/authority/<expected-stage>`
- **THEN** the workflow MUST return a structured redacted failure before accepting any record from that directory

#### Scenario: Git path transport is not lossless

- **WHEN** a NUL-delimited Git path cannot be strictly and reversibly represented without replacement or byte loss
- **THEN** the workflow MUST fail closed before scope comparison
- **AND** it MUST NOT discard or lossy-normalize the path

#### Scenario: Allowed path rules are malformed

- **WHEN** `allowed_path_rules` has a wrong container or member type, a non-string element, or an invalid exact/prefix value
- **THEN** the workflow MUST return a structured redacted failure without traceback
- **AND** no action may proceed with a partially interpreted rule set

#### Scenario: Merge and push are bound to final reviewed content

- **WHEN** the workflow reaches merge or push preflight
- **THEN** the exhaustive current change manifest MUST equal the final independently reviewed manifest and the actual review-set packet MUST match the host-retained reviewed packet
- **AND** only the schema-valid review-set and delivery-binding evidence tail may postdate that packet
- **AND** any other post-review change MUST reopen the affected gates

#### Scenario: Push uses an exact candidate and exact old remote tip

- **WHEN** the workflow performs an authorized push
- **THEN** current HEAD MUST equal the host-retained exact candidate HEAD, the authorized remote tip MUST be its ancestor, and the explicit ref update MUST use an exact-old-OID lease
- **AND** a remote-tip race, ambiguous endpoint, or non-fast-forward target MUST stop without automatic history changes

#### Scenario: Ambiguous push outcome remains unknown

- **WHEN** a push may have reached the server but the client cannot prove the final remote ref
- **THEN** `vcs_pushed` MUST remain `unknown`
- **AND** the workflow MUST reconcile by read-only query of the same effective push endpoint before retrying

#### Scenario: Post-merge P1 reopens closeout

- **WHEN** formal review after merge discovers a P1 finding
- **THEN** `.harness/review_checklist.md` and `docs/PROGRESS.md` record the blocker
- **AND** `HANDOFF_TO_NEXT_CHAT.md` records it when it changes the next session's safe action
- **AND** the next stage remains blocked until remediation, re-review, and verification complete

#### Scenario: Delivery verdicts remain distinct

- **WHEN** the stage reports closeout state
- **THEN** `technical_ready`, `human_authorized`, and `vcs_pushed` are evaluated separately, with `vcs_pushed` distinguishing `not_attempted`, `unknown`, and `verified`
- **AND** no repository-authored receipt or passing technical gate alone can assert live human authorization or remote push success
