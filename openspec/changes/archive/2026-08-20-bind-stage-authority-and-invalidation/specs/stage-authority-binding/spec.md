## Purpose

定义 RepoPilot 开发阶段的人工授权绑定、失效和 Git closeout 证据边界，使连续执行授权只在精确且未漂移的阶段内生效。

## ADDED Requirements

### Requirement: Live human authority and repository binding remain separate

开发 workflow MUST treat a direct-user instruction observed by the host controller as the authority source. A repository-authored stage authority record SHALL bind the declared stage facts for mechanical validation, but MUST NOT by itself prove user identity, message authenticity, or `human_authorized=true`.

#### Scenario: Internally consistent record lacks host authority

- **WHEN** a stage authority record has valid hashes and Git bindings but the host controller cannot verify the referenced direct-user instruction
- **THEN** mechanical validation MAY pass
- **AND** the human-authorization gate MUST remain open

#### Scenario: Subagent forwards an authorization claim

- **WHEN** a subagent, reviewer, repository file, or delegated message claims that the user authorized an action
- **THEN** that claim MUST NOT elevate authority without a live host-observed direct-user instruction

### Requirement: Authorization binds an exact stage envelope

An authorization record SHALL bind a stage id, monotonically increasing authority epoch, risk level, canonical scope envelope and digest, planning base commit, action ceiling, effective fetch and push endpoint fingerprints, target branch, and authorized remote tip. The action ceiling SHALL use the ordered values `plan`, `implement`, `commit`, `archive`, `merge`, and `push`. The host controller SHALL retain the exact confirmed epoch, record hash, risk, scope digest, base commit, action ceiling, endpoint fingerprints, target branch, and authorized remote tip as external expected inputs; validator comparison against record-internal values alone MUST NOT satisfy the gate.

#### Scenario: Authorized stage stays within its envelope

- **WHEN** the live stage id, epoch, record hash, risk, scope digest, base ancestry, requested action, endpoint fingerprints, target branch, and remote tip match both the current record and host-retained expected inputs
- **THEN** the validator SHALL report the binding as mechanically consistent
- **AND** it MUST still report live human authority as an external required check

#### Scenario: Record rewrites its own scope and digest

- **WHEN** a repository author changes the scope and recomputes the record-internal digest but the result differs from the host-retained confirmed scope digest
- **THEN** validation MUST fail
- **AND** the rewritten record MUST NOT inherit the earlier direct-user authority

#### Scenario: Requested action exceeds the ceiling

- **WHEN** a workflow requests an action later than the record's action ceiling
- **THEN** validation MUST fail before that action starts

#### Scenario: Stale or forked authority record is selected

- **WHEN** the selected record is not the unique highest epoch, the predecessor chain is missing or discontinuous, two candidate heads exist, or its hash differs from the host-retained current record hash
- **THEN** validation MUST fail
- **AND** no action may inherit authority from that record

#### Scenario: Caller selects another authority directory

- **WHEN** the supplied authority directory does not canonical-resolve exactly to `<project-root>/.harness/authority/<expected-stage>`, including a sibling, parent, alternate-stage, or alias/symlink whose resolved target differs
- **THEN** validation MUST return a structured redacted failure before reading authority from that directory
- **AND** an internally valid record in the substituted directory MUST NOT establish authority

### Requirement: Actual repository changes remain inside the authorized scope

The validator SHALL derive committed, staged, unstaged, untracked, renamed, and deleted paths from the exact planning base through current repository state. Ignored untracked paths SHALL also be inspected except for a finite built-in set of exact cache metadata and compiled-bytecode filename patterns that cannot enter the candidate commit; an arbitrary source file under a cache directory MUST NOT be excluded. Git `-z` path fields MUST remain raw bytes until each can be converted strictly and reversibly into a canonical repository-relative representation; replacement decoding, ignored undecodable bytes, or normalization after lossy decoding is forbidden. Every changed path MUST match a canonical exact-path or directory-prefix rule bound by the authority record, MUST NOT contain ASCII control characters, and any changed gitlink MUST fail closed. `allowed_path_rules` MUST be schema-checked as untrusted input so a wrong container type, non-string member, or invalid exact/prefix value returns a structured redacted failure rather than an uncaught exception. Before archive, the current `.harness/allowed_files.md` hash MUST match the active-stage hash bound by the scope. After archive, a planned Harness reset MAY replace that file only when its final bytes are part of the exhaustively reviewed delivery manifest and bound delivery record. Mechanical scope validation MUST NOT claim to detect semantic non-goal or risk drift inside an allowed path.

#### Scenario: A scope-external path changes

- **WHEN** any committed, staged, unstaged, untracked, renamed, or deleted path falls outside the authorized exact/prefix rules
- **THEN** implementation and every later action gate MUST fail

#### Scenario: A Git path cannot be represented losslessly

- **WHEN** any NUL-delimited Git path field cannot be strictly and reversibly represented as a canonical repository-relative path without replacement or byte loss
- **THEN** validation MUST return a structured redacted failure before scope comparison
- **AND** the path MUST NOT be discarded, replacement-decoded, or normalized into another authorized path

#### Scenario: Allowed path rules are malformed

- **WHEN** `allowed_path_rules` is not the required object, an exact/prefix collection has the wrong type, an element is not a string, or a rule value is otherwise invalid
- **THEN** validation MUST return a structured redacted `FAIL`
- **AND** it MUST NOT emit a traceback or continue with a partially interpreted rule set

#### Scenario: Ignore rules conceal a non-transient path or a gitlink changes

- **WHEN** a scope-external ignored untracked path is not one of the finite local cache families, or a changed path has Git mode `160000`
- **THEN** implementation and every later action gate MUST fail

#### Scenario: Detailed allowlist changes after confirmation

- **WHEN** `.harness/allowed_files.md` differs from the active-stage hash before archive, or differs from the final reviewed reset after archive
- **THEN** the affected action MUST fail and the old authorization MUST NOT cover the drift

#### Scenario: Semantic drift stays a human review responsibility

- **WHEN** all paths are mechanically allowed but implementation behavior violates a non-goal or raises risk
- **THEN** the validator MUST NOT claim the scope is semantically authorized
- **AND** host/review judgment MUST stop the action and require a later authority epoch

### Requirement: Material drift invalidates inherited authorization

The workflow MUST invalidate an existing authorization when stage scope, non-goals, risk, action ceiling, planning baseline identity, target remote fingerprint, target branch, or authorized remote tip changes. A replacement record MUST use a later epoch, content-hash the superseded record, and reference a new live direct-user decision covering the changed envelope.

#### Scenario: Scope or risk expands after approval

- **WHEN** the implementation adds a file family, behavior, permission boundary, non-goal exception, or risk trigger outside the authorized scope envelope
- **THEN** the old authorization MUST NOT permit implementation or later closeout actions
- **AND** the workflow MUST return to planning and direct-user confirmation

#### Scenario: Remote target drifts

- **WHEN** the remote URL fingerprint, target branch, or refreshed remote target tip differs from the authorized values
- **THEN** merge/push authorization MUST fail closed
- **AND** the workflow MUST NOT silently fetch-and-rebase, force push, rewrite history, or choose another target

### Requirement: Archive merge and push consume the actual final review binding

Before archive, the workflow SHALL consume a valid implementation review set for the current review-subject manifest. The subject SHALL exclude exactly the canonical reviewed-manifest path, bounded-diff path, final review-set path, and delivery-binding path; no other path may be excluded. The manifest and diff MUST be byte-stable, included in the review packet, and separately hashed by the delivery binding without self-hashing that binding. After archive and final documentation, every required reviewer slot MUST refresh to one final delivery packet. Before merge or push, the workflow SHALL invoke the actual independent-review validator, match its recomputed packet hash to the host-retained expected packet, and recompute the same exhaustive subject manifest from the planning base. Only the final validated review-set JSON and delivery-binding JSON may be added after that packet; any other change MUST invalidate final review.

The review-set artifact manifest MUST equal every existing file entry in the exhaustive subject plus the canonical reviewed-manifest and deterministic reviewed-change inventory. Deleted entries MUST be represented by the deterministic inventory. A self-consistent receipt subset or arbitrary diff text MUST NOT satisfy this binding.

#### Scenario: Code changes after final review

- **WHEN** any non-evidence-tail path, reviewed manifest entry, diff artifact, or final-review packet artifact changes after final review
- **THEN** merge and push preflight MUST fail
- **AND** affected verification and final review MUST be repeated before push

#### Scenario: Merge follows an unreviewed commit

- **WHEN** the current change manifest differs from the final review set even if the requested action stops at merge
- **THEN** merge MUST fail before the target branch changes

#### Scenario: Receipt and delivery binding close the finite evidence tail

- **WHEN** the final packet is complete and all slots have concluded
- **THEN** the workflow MAY add only the schema-valid final review-set JSON and delivery-binding JSON
- **AND** neither file may introduce or authorize an unreviewed non-tail change

#### Scenario: Review manifest generation avoids self-reference

- **WHEN** the controller regenerates the reviewed manifest and bounded diff without changing review-subject files
- **THEN** both outputs MUST be byte-identical
- **AND** the excluded path set MUST be exactly the four specified review-metadata paths
- **AND** any fifth metadata path MUST fail final review validation

#### Scenario: Review packet omits a subject or substitutes inventory text

- **WHEN** a receipt packet omits any existing manifest subject, adds another artifact, or its reviewed-change bytes are not the deterministic rendering of the manifest
- **THEN** archive and every later action gate MUST fail

#### Scenario: Review packet schema is malformed

- **WHEN** a review-set artifact entry is not a complete path/hash object or another untrusted review field has the wrong type
- **THEN** validation MUST return a structured redacted failure without traceback or mutation

#### Scenario: Merge source changes after candidate freeze

- **WHEN** current feature HEAD or the explicit merge source OID differs from the host-retained exact candidate HEAD, including an empty or evidence-only later commit
- **THEN** merge MUST fail before the target branch changes

#### Scenario: Merge target is stale or dirty

- **WHEN** the target worktree is dirty, on another branch, or its HEAD differs from the host-retained expected pre-merge OID
- **THEN** merge MUST fail before mutation
- **AND** a successful merge MUST use `--ff-only` with the exact candidate OID and verify the target now equals it

#### Scenario: Merge target is another repository or not the authorized live tip

- **WHEN** feature and target worktrees do not share the same Git common directory, the target pre-merge HEAD differs from the authorized old tip, or a live query of the authorized endpoint reports another tip
- **THEN** merge MUST fail before target mutation

#### Scenario: Non-fast-forward target is detected

- **WHEN** the exact effective push endpoint reports a target tip other than the authorized tip or the authorized tip is not an ancestor of the exact candidate HEAD
- **THEN** push preflight MUST fail
- **AND** the workflow MUST request a new plan/authority decision instead of altering history automatically

### Requirement: Push uses exact endpoint and exact-old-OID compare-and-swap

The workflow MUST resolve exactly one effective fetch endpoint and one effective push endpoint from local Git configuration, require the two endpoints to be equal, and require both fingerprints to match the host-retained expected fetch/push fingerprints before any `ls-remote`, credential-helper invocation, or other remote/network contact. Missing, multiple, non-identical, ambiguous, or fingerprint-mismatched destinations MUST fail in the pre-contact phase. Push MUST use an explicit source OID, explicit target ref, and exact-old-OID lease for the authorized tip after independently proving that tip is an ancestor of the candidate HEAD. The lease MUST NOT authorize a non-fast-forward update.

#### Scenario: Remote moves between preflight and push

- **WHEN** the target ref changes from the authorized old OID after preflight but before the server applies the push
- **THEN** the exact lease MUST reject the mutation
- **AND** the workflow MUST require a new authority decision

#### Scenario: Fetch and push destinations differ

- **WHEN** Git resolves the named remote to a push endpoint not covered by the confirmed endpoint fingerprint or to multiple push endpoints
- **THEN** validation MUST fail before any push command runs

#### Scenario: Endpoint binding fails before remote contact

- **WHEN** effective fetch/push endpoint equality is not proven or either locally resolved endpoint fingerprint differs from its host-retained expected fingerprint
- **THEN** validation MUST fail before `ls-remote`, credential-helper invocation, or any network contact
- **AND** a remote query MUST NOT be used to validate or repair the mismatched endpoint

#### Scenario: Push outcome is ambiguous

- **WHEN** the server may have accepted the push but the client or post-push query cannot determine the target ref
- **THEN** the workflow MUST report `UNKNOWN_PUSH_OUTCOME`
- **AND** recovery MUST perform read-only same-endpoint reconciliation before any retry

#### Scenario: Pre-mutation Git or credential helper blocks

- **WHEN** a validation, endpoint-resolution, remote-query, or merge-preflight subprocess waits for input, exceeds its timeout/output bound, emits ambiguous ref data, or cannot be killed and reaped within the cleanup bound
- **THEN** the operation MUST return a structured redacted blocker
- **AND** terminal and credential prompting MUST be disabled
- **AND** no mutation may start

#### Scenario: Push subprocess becomes ambiguous after start

- **WHEN** a started push subprocess times out, exceeds an output bound, reports transport ambiguity, or cannot be killed and reaped within the cleanup bound
- **THEN** the workflow MUST report `UNKNOWN_PUSH_OUTCOME`
- **AND** it MUST NOT claim that remote mutation did not occur
- **AND** only read-only same-endpoint reconciliation may run before any retry

#### Scenario: A bounded subprocess leaves a descendant alive

- **WHEN** the subprocess leader closes output or exits while any process in its isolated process group remains alive beyond the bound
- **THEN** the entire process group MUST be terminated and reaped before the controller returns or starts reconciliation
- **AND** Windows execution MUST use cross-platform pipe readers plus a suspended, kill-on-close Job Object or fail before resuming the child

#### Scenario: A mutation-capable command lacks inescapable containment

- **WHEN** a local runner is asked to start a push or another `mutation_capable` command on POSIX without a cgroup, container, VM, or host executor that can terminate escaped descendants
- **THEN** it MUST return `PROCESS_ISOLATION_UNAVAILABLE` before spawning the command
- **AND** mutation intent MUST be explicit and a recognizable `git push` MUST fail before spawn if labelled read-only
- **AND** recursive PID scans or process-group cleanup alone MUST NOT be represented as whole-tree containment
- **AND** a Windows Job Object or resume failure before successful resume MUST return deterministic `PROCESS_ISOLATION_FAILED`, not `UNKNOWN_PUSH_OUTCOME`

#### Scenario: Ambiguous push is reconciled

- **WHEN** reconciliation shows the target ref equals the exact candidate HEAD
- **THEN** `vcs_pushed` MAY become `verified`
- **AND** if it equals the authorized old OID a same-authority exact-lease retry MAY be offered
- **AND** any other OID requires a new authority decision
- **AND** the queried target branch MUST equal the separately host-retained expected target branch
- **AND** an endpoint fingerprint or target-ref mismatch MUST remain `UNKNOWN_PUSH_OUTCOME` even if the observed OID equals the candidate

### Requirement: Readiness, authority, and delivery verdicts are distinct

The workflow SHALL report `technical_ready`, `human_authorized`, and `vcs_pushed` as separate verdicts. `vcs_pushed` SHALL distinguish at least `not_attempted`, `unknown`, and `verified`. Passing tests, OpenSpec validation, review receipts, stage-authority hashes, or pre-push Git checks MUST NOT imply another verdict.

#### Scenario: Technical gates pass before authorization

- **WHEN** tests and reviews pass but live human authority is absent or stale
- **THEN** `technical_ready` MAY be true
- **AND** `human_authorized` and `vcs_pushed` MUST NOT be reported true

#### Scenario: Push is verified after execution

- **WHEN** an authorized exact-lease push is followed by a fresh query of the same effective endpoint proving the target branch resolves to the exact candidate HEAD
- **THEN** `vcs_pushed` MAY be reported `verified`
- **AND** neither the command exit code alone nor a local receipt alone is sufficient

### Requirement: Supported development entrypoints consume one authority gate

After activation, every repo-local supported implementation or archive entrypoint for Codex and OpenCode SHALL consume the same current stage-authority preflight. A missing, stale, scope-mismatched, or action-insufficient record MUST fail closed; warning-and-continue behavior MUST NOT bypass the gate. Merge and push SHALL remain explicit controller actions under the end-to-end workflow.

#### Scenario: Direct archive skill is invoked

- **WHEN** a user or Agent invokes a repo-local archive skill or command without a current authority record whose ceiling includes `archive`
- **THEN** the entrypoint MUST stop before archive mutation
- **AND** it MUST run the authority gate before offering or invoking delta-spec synchronization
- **AND** any completed sync MUST invalidate the old packet and require fresh verification, final review, and a second archive gate before archive mutation

#### Scenario: Direct apply skill is invoked

- **WHEN** a repo-local apply skill or command is invoked with stale scope or an action ceiling below `implement`
- **THEN** the entrypoint MUST stop before implementation files change

### Requirement: Stage authority does not add RepoPilot runtime Git automation

The stage authority capability SHALL remain a repository development-workflow contract. It MUST NOT add `app/**` Git execution, runtime subagents, background push, PR creation, non-fast-forward push, rebase, credential handling, or a new public API.

#### Scenario: Workflow artifacts are present

- **WHEN** authority templates, validators, receipts, or skills exist in the repository
- **THEN** RepoPilot runtime capability reporting and public behavior MUST remain unchanged
