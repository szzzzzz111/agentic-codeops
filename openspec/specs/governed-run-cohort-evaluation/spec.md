# governed-run-cohort-evaluation Specification

## Purpose
Define the development-time one-shot evidence boundary for observing one host-managed Codex App coding task and binding its exact
completion mutation to same-snapshot verification, without elevating repository-authenticated provenance, task completion, product
acceptance, runtime integration, or Git delivery.

## Requirements

### Requirement: Codex App host-managed one-shot boundary

The evaluation SHALL use exactly one fresh Codex App task created without the current implementation conversation and exactly one
App-managed Git worktree at the frozen planning base. The repository script MUST NOT create a task, call Codex App task tools, start
`codex exec`, contact a provider, inherit `CODEX_HOME`, or claim RepoPilot runtime subagent integration.

#### Scenario: New task replaces local CLI producer

- **WHEN** the authorized experiment starts
- **THEN** the external controller creates one fresh Codex App task and one App worktree
- **AND** the repository script starts no Codex/provider process
- **AND** failure to create or correlate that task yields `NOT_OBSERVED` without fallback to local CLI

### Requirement: Clean handshake precedes the only coding turn

The task creation turn SHALL only reply `READY_FOR_TASK` and SHALL NOT modify files or commit. After that turn, the controller MUST
prove the stage and task worktrees are live, non-prunable registrations in the same `git worktree list --porcelain` result, the task is
clean, and it has exact HEAD
`b7a8439fac9013f5ad59c308c4b16d333d466ddb` before sending the coding prompt.
Unrelated prunable historical records SHALL be excluded from the live registration set; they MUST NOT substitute for either required
stage/task registration or cause an otherwise valid pair to fail.

The only coding prompt SHALL require changing only the first line of `README.md` from `# RepoPilot` to
`# RepoPilot Agent Probe`, forbid commit and other changes, and require the final reply to be exactly `READY_FOR_REVIEW`.
This mutation authority SHALL apply only to the separately correlated task-worktree role. It SHALL bind the complete file from
SHA-256 `70e242e898295dffaeb9a9723c5536edb96b5b6429e94fea274925a4a8b4e64e` to
`d7844da1d65cabe3307959c6ac9a510e483bcdb99ad5070b280bdea0c33d575c`; it MUST NOT authorize the stage implementer to
modify the stage worktree's `README.md`.

#### Scenario: Handshake changes the worktree

- **WHEN** any path changes before the coding prompt
- **THEN** the controller MUST NOT send the coding prompt
- **AND** the experiment is `NOT_OBSERVED` or failed without retry

#### Scenario: Clean handshake allows one coding turn

- **WHEN** the handshake completes with exact `READY_FOR_TASK` and the baseline checks pass
- **THEN** the controller sends the one fixed coding prompt once
- **AND** it does not send a second coding turn, retry, resume, or changed prompt

### Requirement: Host task observation is bounded and source-unverified

The bridge SHALL accept exactly one bounded, EOF-delimited JSON object containing only the fixed schema version, the expected thread id,
`terminal_status=completed`, and `final_text=READY_FOR_REVIEW`. It MUST reject unknown/missing fields, invalid types, mismatched
thread ids, other terminal states, other final text, blank or oversized input, duplicate input, trailing data, an unclosed channel, and
channel timeout. The controller MUST close stdin after writing the unique record.

The canonical observation digest MAY bind an `AgentClaim`, but repository bytes MUST NOT claim native host provenance. The summary
MUST set `source_provenance=host_observed_unverified`; only the external controller's create/wait/read metadata may support the
statement that a real task was observed.

#### Scenario: Deterministic injected observation

- **WHEN** tests inject a schema-valid observation without native host metadata
- **THEN** they may prove the adapter and kernel chain
- **AND** they MUST NOT independently prove a real Codex App task existed

#### Scenario: Observation correlation fails

- **WHEN** terminal status, final text, thread id, schema, input count, input size, EOF closure, or bounded wait is invalid
- **THEN** no ready claim or verification receipt is produced
- **AND** the result fails closed without a second task or turn

### Requirement: Exact worktree mutation and snapshot-bound verification

The bridge SHALL retain the clean baseline snapshot and baseline `README.md` bytes in one process. Completion MUST keep the same
repository id and HEAD, contain no untracked or index drift, change only `README.md`, and equal the exact frozen first-line
replacement. Any other bytes or paths MUST fail before verification.

The bridge SHALL run the existing whitelist `ruff` label with no additional argv and SHALL force `RUFF_NO_CACHE=true` before invoking
the existing runner. A real-runner test SHALL begin without `.ruff_cache`, run the whitelist label, and prove no cache was created.
The runner-before and post-verification snapshots MUST equal the claim-bound completion snapshot before a `VerificationReceipt` is
created.

#### Scenario: Exact task result reaches review readiness

- **WHEN** the real host observation is completed with exact `READY_FOR_REVIEW`, the exact README mutation is present, `ruff`
  succeeds, and all endpoint snapshots match
- **THEN** the existing evaluator returns `ready_for_review` with `VERIFICATION_PASSED`
- **AND** the summary binds observation, claim, snapshot, verification-result, and receipt digests

#### Scenario: Scope or snapshot drifts

- **WHEN** the stage worktree README changes, or the task worktree has an untracked path, index drift, another tracked path, wrong
  README bytes/digest, HEAD/repository/live-registration mismatch, verifier cache write, or verification-time snapshot change
- **THEN** the experiment fails closed and MUST NOT claim review readiness

### Requirement: Six failure families stop without platform expansion

The evaluation SHALL deterministically cover task/observation lifecycle, baseline/worktree identity, claim correlation, mutation scope,
snapshot continuity, and verification/receipt/evaluator failure families. Any failure SHALL stop the one-shot attempt without retry,
resume, replacement task, local CLI fallback, VM/container, credential proxy, global registry, daemon, or background supervisor.

#### Scenario: Host capability is insufficient

- **WHEN** task terminal metadata or the App worktree cannot be correlated precisely
- **THEN** the result is `NOT_OBSERVED`
- **AND** the stage does not add another execution platform

### Requirement: Claim ceiling remains below completion and delivery

Even when the evaluator returns `ready_for_review`, the summary MUST keep `task_complete=false`, `semantic_completion=false`,
`human_review=NOT_OBSERVED`, `product_acceptance=false`, `runtime_integration=false`, and
`git_delivery_authorized=false`. It MUST state that snapshot continuity proves stable endpoint samples only and does not prove OS-level
isolation, perfect ABA absence, authenticated provenance, semantic correctness, product acceptance, archive, commit, merge, or push.

#### Scenario: Mechanically successful one-shot experiment

- **WHEN** the host-managed task and same-snapshot verification chain succeed
- **THEN** the strongest result is one host-observed, source-unverified `ready_for_review` experiment
- **AND** no completion, acceptance, runtime, security, or Git-delivery claim is elevated
