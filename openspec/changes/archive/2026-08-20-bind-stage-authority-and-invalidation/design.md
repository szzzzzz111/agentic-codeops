## Context

See `proposal.md` for motivation. The current workflow already separates OpenSpec planning, independent review, implementation, archive, merge, and push, and it correctly says continuous authorization does not remove formal gates. The remaining gap is that the authorization is not bound to a canonical stage envelope and Git target, so a later agent could preserve internally consistent receipts while changing what is being authorized.

The design must coexist with the independent-review validator's claim ceiling: repository-authored JSON and hashes can prove content consistency, not host identity, message provenance, or chronology. It must also preserve the product boundary: RepoPilot runtime intentionally does not commit, merge, push, or dispatch runtime subagents.

## Goals / Non-Goals

**Goals:**

- Bind a direct-user decision to one exact development stage, risk, scope, action ceiling, baseline, and Git target.
- Fail closed on material stage or Git drift, with an explicit later authority epoch for any replacement decision.
- Bind merge/push to an exhaustively reviewed change manifest, an exact local candidate HEAD, and an exact-old-OID remote lease.
- Give tests and reviewers a deterministic, provider-neutral contract without claiming machine-proven human identity.
- Keep the mechanism lightweight: an append-only authority envelope, one delivery binding, one validator, live Git commands, and workflow wiring.

**Non-Goals:**

- No hosted approval service, signature infrastructure, identity provider, approval database, WAL, scheduler, or Greenfield control plane.
- No RepoPilot runtime changes, `app/**` Git automation, runtime subagent, connector, MCP server, background task, notification, or public API.
- No automatic fetch/rebase/merge conflict repair, non-fast-forward update, branch deletion, PR creation, credential setup, or history rewrite. An exact-old-OID lease is allowed only after ancestry proves the update is fast-forward.
- No claim that a record created by an Agent proves a user authored or approved its contents.

## Decisions

### Decision 1: Use three evidence layers with explicit claim ceilings

The workflow will distinguish:

1. **Live host authority**: the controller observes a direct-user instruction and decides whether it covers the frozen stage envelope. This is the only source for `human_authorized`.
2. **Repository mechanical binding**: a canonical JSON record binds the facts the controller says were authorized. The validator can report only `mechanical_consistency_only` and must keep `human_authorized=false`/external.
3. **Live Git evidence**: read-only Git commands prove the current local/remote-tracking state used by action preflight and post-push verification.

Subagent messages, reviewer receipts, hashes, tests, or repository fields cannot elevate layer 2 into layer 1. Alternative rejected: label a SHA-256 receipt as signed human authority. A public content hash authenticates content equality, not signer identity.

### Decision 2: Split immutable human authority from later delivery evidence

Human authority is stored as append-only `.harness/authority/<stage-id>/epoch-NNNN.json` records. Each record includes:

- `schema_version`, `stage_id`, `authority_epoch`, and `supersedes_record_sha256` for every epoch after 1;
- `authority_source.kind=host_direct_user_instruction` and a bounded opaque `host_reference`, without message body;
- `scope`: risk, summary, canonical exact/prefix allowed-path rules, canonical non-goals, the active-stage `.harness/allowed_files.md` hash, and `scope_sha256` over that object;
- `planning_baseline`: exact base commit;
- `action_ceiling`: one ordered value from `plan` through `push`;
- `vcs_target`: remote name, resolved effective fetch URL fingerprint, resolved effective push URL fingerprint, target branch, and authorized remote tip.

The authority directory is a linear log: filenames are exact zero-padded epochs, every predecessor must exist, hashes must chain, the highest epoch is the only current head, and unexpected JSON/symlink/fork-like names fail closed. The host retains the exact current epoch and record hash. The record is immutable after implementation begins.

Later review/push facts use a separate `.harness/authority/<stage-id>/delivery-binding.json`; they never rewrite the human authority record. This avoids pretending the user pre-approved a future commit hash and avoids a record containing the hash of a commit that contains itself.

At the L3 confirmation gate the controller presents and retains the exact record hash/epoch, risk, scope digest, planning base, action ceiling, effective fetch/push URL fingerprints, target branch, and authorized remote tip. These values are not recovered solely from the record being validated. Canonical JSON uses UTF-8, sorted keys, compact separators, canonical sorted arrays, lowercase hashes, and no unknown/security-sensitive fields.

Alternative rejected: one mutable record with final HEAD and checklist booleans. It creates stale-record selection, fork, and commit self-reference problems.

### Decision 3: Close the scope loop against the real Git change set

The record's path rules use only exact file paths and directory prefixes; arbitrary glob syntax is excluded. The validator recomputes every changed path from the planning base through committed HEAD plus staged, unstaged, untracked, and non-transient ignored worktree state. The only ignored exceptions are exact cache metadata names and compiled-bytecode filename patterns; arbitrary source under a cache directory remains visible, and any staged member is detected normally. Rename and deletion source/destination paths are included. Paths must be canonical POSIX repository-relative values without ASCII control characters, and submodule/gitlink or symlinked control-artifact paths fail closed.

Every changed path must match an authorized exact/prefix rule. For `implement`, ordinary `commit`, and pre-archive checks, the validator also re-hashes `.harness/allowed_files.md` against the active-stage hash. After archive, the reviewed delivery packet may contain the planned reset of Harness files; merge/push validate those final bytes through the exhaustive reviewed manifest and delivery binding instead of requiring the obsolete active-stage hash. A path-rule change always requires new authority. Semantic non-goal/risk drift inside an allowed path remains a host/final-review judgment; the mechanical report must state that ceiling.

Alternative rejected: validate only record-internal scope fields. The same author could keep the record unchanged while changing an unauthorized path.

### Decision 4: Consume the actual independent-review set without exact-HEAD self-reference

Before formal review, the controller creates a canonical `reviewed-change-manifest.json` covering every review-subject change from the planning base: path, change kind, and content hash or deletion marker. The review-subject set excludes exactly four closed review-metadata paths:

- `.harness/reviews/<stage-id>/implementation/reviewed-change-manifest.json`;
- `.harness/reviews/<stage-id>/implementation/reviewed-change.diff`;
- `.harness/reviews/<stage-id>/implementation/review-set.json`;
- `.harness/authority/<stage-id>/delivery-binding.json`.

No other path is implicitly excluded. The first two metadata files are generated before review, are byte-stable on repeated generation, and are themselves included and hashed as review packet artifacts. The review packet artifact set must equal every existing file entry in the manifest plus those two metadata files; deleted paths are bound by the deterministic inventory. A self-consistent subset, arbitrary inventory text, malformed artifact entry, or control-character row injection fails with a structured report. The final review-set and delivery-binding files are the only post-packet evidence tail. The delivery binding hashes the manifest, diff, and review set but does not attempt to hash itself. The exact candidate HEAD retained by the host later binds its final bytes without self-reference.

For `archive`, the validator consumes an actual mechanically valid implementation review set and the existing external dispatch/activation checks. After archive and final documentation are prepared, every required reviewer slot refreshes its final receipt to the same post-archive delivery packet. Only two closed evidence-tail files may be written afterward:

- `.harness/reviews/<stage-id>/implementation/review-set.json`;
- `.harness/authority/<stage-id>/delivery-binding.json`.

Both have deterministic schemas and hashes. The delivery binding also records the final reviewed Harness reset hashes. For `merge` and `push`, the authority validator invokes the existing independent-review validator, requires its recomputed packet hash to equal the host-retained expected implementation packet hash, regenerates the review-subject manifest using the same exact four-path exclusion, and permits no unreviewed subject change or unexpected review metadata. Merge and push therefore use the same final reviewed content even though the final commit also contains the two self-describing evidence-tail files.

The host retains the exact candidate HEAD after the finite final commit and passes it as an external technical preflight input. The repository record does not contain that HEAD. Alternative rejected: require a committed receipt to contain the hash of the commit that contains the receipt.

### Decision 5: Validate the full host-retained envelope and action-specific Git state

`scripts/validate_stage_authority.py` accepts project root, authority directory, required action, expected stage, expected epoch, expected authority-record hash, expected risk, expected scope digest, expected planning base, expected action ceiling, expected remote name, expected effective fetch/push URL fingerprints, expected target branch, and expected authorized remote tip. Merge/push also require the actual implementation review-set path, required review slot count, host-retained reviewed packet hash, and expected candidate HEAD. None of these expected values may be copied from the record by the gate implementation.

The authority directory is not caller-selectable provenance. Before reading an epoch, the validator resolves both paths and requires `authority_dir.resolve()` to equal the canonical resolved `<project-root>/.harness/authority/<expected-stage>` exactly. A sibling, parent, alternate stage, or alias/symlink whose resolved target differs fails with a structured redacted report even if its records are internally valid.

All actions validate linear authority lineage, scope/path closure, base existence/ancestry, and the requested action ceiling. Remote endpoint/tip checks are mandatory at merge/push; earlier actions keep the authorized target bound but do not stop unaffected implementation solely because the remote moved.

Git path inventory treats `-z` output as a byte protocol. It retains every raw path field until a strict reversible conversion to canonical repository-relative representation succeeds; replacement decoding, ignored undecodable bytes, or normalization after lossy decode is forbidden. An unrepresentable path fails closed before scope matching. Schema access has the same boundary: malformed `allowed_path_rules`, wrong container/element types, or invalid exact/prefix values produce a structured redacted validation failure rather than a traceback.

Merge requires a clean feature worktree whose current HEAD and explicit merge source OID both equal the host-retained expected candidate HEAD, plus a clean target worktree from the same Git common directory on the exact target branch at the authorized old remote tip. The merge gate resolves and queries the authorized endpoint from that target and requires its live tip to remain the authorized old tip. The controller runs `git merge --ff-only <exact-candidate-oid>` and immediately verifies the target branch equals that OID. An unrelated clone, caller-substituted pre-merge OID, empty commit, or evidence-only commit after candidate freeze therefore fails before target mutation. Push requires the integrated target branch/current HEAD to equal the same candidate and the exact authorized remote tip to be its ancestor.

The report separates `binding_consistent`, `technical_ready`, `human_authorized`, and `vcs_pushed`. The validator owns only mechanical binding; human authority and reviewer dispatch provenance remain external, and technical readiness is consumed rather than invented.

### Decision 6: Bind the actual push endpoint with an exact-old-OID lease

Push handling remains controller-operated:

1. resolve exactly one effective fetch URL and one effective push URL using local Git configuration; require endpoint equality and require both URL fingerprints to match the host-retained expected fetch/push fingerprints before any remote contact;
2. only after step 1 passes, query the exact effective push URL with `git ls-remote` and require the target ref to equal the authorized old OID; if equality or either fingerprint fails, stop before `ls-remote`, credential helper invocation, or any network contact;
3. verify the old OID is an ancestor of the exact candidate HEAD;
4. push the explicit source OID to the explicit target ref with an exact `--force-with-lease=<target-ref>:<authorized-old-oid>` compare-and-swap; this option is permitted only with the preceding ancestry proof and MUST NOT authorize a non-fast-forward update;
5. query the same effective push URL again and require the target ref to equal the exact candidate HEAD before reporting `vcs_pushed=verified`.

The exact lease closes the preflight/push race: any remote movement after step 2 causes the server-side update to fail before ref mutation. URL rewriting is evaluated through Git's effective URL resolution; distinct fetch/push endpoints or multiple destinations fail closed.

If the server may have accepted the push but the client or post-query outcome is ambiguous, state becomes `UNKNOWN_PUSH_OUTCOME`. Recovery itself resolves the host-bound effective push URL fingerprint, requires the requested branch to equal a separately supplied host-retained expected target branch, and queries that exact ref rather than accepting a caller-supplied OID: exact candidate HEAD means verified; exact authorized old OID means not applied and eligible for a same-authority lease retry; any other OID requires new authority. Endpoint/ref mismatch and network/query failure remain unknown and never trigger an automatic second push.

Every Git subprocess used by validation, endpoint resolution, remote query, merge preflight, push, and reconciliation uses fixed argv with `shell=false`, stdin disabled, terminal/credential prompting disabled, an action-specific finite timeout, and bounded threaded stdout/stderr readers. Mutation intent is a required caller input, and a recognizable `git push` may not be under-labelled as read-only. A POSIX process group is sufficient only for read-only commands whose contract does not permit mutation; a descendant can escape it with `setsid()`, so the repository runner refuses every `mutation_capable=true` command before spawn on POSIX until a cgroup/container/VM or host executor supplies an inescapable whole-tree boundary. Windows creates the child suspended, assigns it to a kill-on-close Job Object, and resumes it only after isolation succeeds; failure before successful resume is a deterministic `PROCESS_ISOLATION_FAILED`, not an unknown push. Timeout, output overflow, prompt/helper failure, ambiguous multi-line ref output, or cleanup failure in a pre-mutation validation/query/preflight returns a structured redacted blocker. Once a push has started inside a qualifying containment boundary, any timeout, overflow, transport ambiguity, or cleanup failure yields `UNKNOWN_PUSH_OUTCOME`; the workflow makes no claim that mutation did not occur and performs only read-only same-endpoint reconciliation before any retry. Raw remote output, credential-helper text, local paths, and exception traces are not persisted.

Alternative rejected: ordinary push plus post-query. It can succeed after an unauthorized intermediate remote update that remains an ancestor of local HEAD.

### Formal Re-review Remediation Status

The four P1 contract remediations for pre-contact endpoint validation, exact authority-directory identity, lossless Git `-z` path handling, and structured malformed-rule failure are `waiting re-review`. Documentation/spec projection does not verify or close any finding.

### Decision 7: Wire every supported workflow entrypoint and activate prospectively

The shared authority preflight is required not only in `repo-stage-workflow`, but also in repo-local Codex/OpenCode apply and archive skills/commands. Missing/stale authority fails closed after activation; direct invocation may not bypass it. Archive entrypoints run the gate before offering or invoking delta-spec synchronization, because sync is itself a pre-archive mutation. Any completed sync invalidates the pre-sync manifest and receipts, so affected verification, every final review slot, and the archive gate repeat before archive mutation. Merge/push remain controller actions under `repo-stage-workflow` and have no separate automation entrypoint.

This change's plan gate uses the already-active independent-review workflow plus the existing L3 human confirmation rule. The new authority validator cannot retroactively prove that it authorized its own implementation. After schema, negative tests, all supported entrypoint wiring, and focused verification pass, the pre-change process authority may activate it for this change's archive/merge/push and subsequent stages. The activation record can be content-hashed, but the repository validator cannot prove activation chronology.

## Risks / Trade-offs

- [A malicious controller can forge repository records] → keep live human authority external and never emit `human_authorized=true` from repository validation.
- [Remote queries are network-dependent] → use the exact effective push endpoint; an unavailable or ambiguous query blocks mutation or leaves `UNKNOWN_PUSH_OUTCOME`.
- [Remote can change after preflight] → exact-old-OID lease provides server-side compare-and-swap, while an independent ancestry check preserves fast-forward-only behavior.
- [Exact remote-tip binding is conservative] → treat any remote movement as a new planning/authority decision instead of silently rebasing or force pushing.
- [Stage scope manifests can become verbose] → use only exact/prefix rules and an exhaustive machine-generated change manifest; do not add a general policy language.
- [Evidence-tail files are not inside their own reviewed packet] → permit exactly two deterministic JSON files after the final packet and validate both; any other post-review change reopens review.
- [Two Codex reviewers share model correlation] → use distinct empty-context instances, keep them blind to each other, and record residual same-model uncertainty.

## Migration Plan

1. Freeze proposal/design/tasks/spec/Harness planning artifacts and run internal review plus two empty-context independent plan reviews under the current review gate.
2. Obtain explicit L3 human confirmation of the final plan; this direct-user decision remains the pre-change implementation authority.
3. Add RED tests, then the authority template/validator and workflow wiring.
4. Run negative tests, focused verification, structural checks, and full available repository verification.
5. Record pre-change authority activation after all supported entrypoints are wired; use it prospectively for this stage's archive/merge/push and later stages.
6. Run high-risk implementation review, archive, prepare final delivery artifacts, refresh every reviewer slot to one final packet, and write only the two validated evidence-tail files afterward.
7. Create the finite candidate commit, retain its exact HEAD in host state, merge with the same reviewed manifest, then use exact-endpoint/exact-lease push and read-only postcondition reconciliation.

Rollback removes the new validator/template/wiring and restores the prior process spec. No runtime or persistent product data migration exists.

## Open Questions

None. The direct user renewed L3 confirmation for the corrected envelope; any later envelope drift requires another authority decision.
