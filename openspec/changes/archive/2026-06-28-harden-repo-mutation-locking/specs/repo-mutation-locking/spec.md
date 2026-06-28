## ADDED Requirements

### Requirement: RepoPilot Mutations Acquire A Repo-Scoped Lock

系统 SHALL require RepoPilot-owned mutation flows that can write repository files,
Git worktree metadata, or patch/worktree lifecycle state to acquire an exclusive
lock for the current normalized `repo_key` before their first mutable preflight.

Whitelisted `verification_run` execution SHALL be treated as write-risk for lock
purposes when it targets the same repository or retained worktree.

The lock MUST be shared across users for the same repository. User authorization,
patch eligibility, and worktree eligibility MUST remain scoped by
`user_id + repo_key`.

#### Scenario: Concurrent mutation is refused

- **WHEN** one RepoPilot mutation flow already holds the repo mutation lock
- **AND** another RepoPilot mutation flow for the same repo starts
- **THEN** the second flow is safely refused before repository mutation
- **AND** it returns through the existing `/chat.answer` contract

#### Scenario: Different repo scopes do not conflict

- **WHEN** two mutation flows target different normalized repo keys
- **THEN** their lock scopes do not conflict solely because their user ids match

### Requirement: Lock Covers Mutable Preflight Through Finalize

系统 SHALL hold the repo mutation lock from the first mutable preflight through
write execution, state finalization, and any required rollback/recovery for each
accepted mutation flow.

For verified patch promotion, the lock MUST be held before checking main
workspace cleanliness and `HEAD == base_commit`, and MUST remain held through
main workspace write, rollback if needed, and patch/worktree terminal state
finalization.

Nested lock acquisition for the same repo_key MUST NOT block indefinitely. A
flow that needs to call an internal mutation helper while already holding the
lock MUST pass existing lock provenance explicitly or refuse safely.

#### Scenario: Promotion base check happens under lock

- **WHEN** a confirmed promotion request reaches main workspace dirty/HEAD checks
- **THEN** those checks run while the repo mutation lock is held
- **AND** the lock remains held until promotion succeeds, fails without mutation,
  or finishes rollback semantics

#### Scenario: Nested same-process acquisition does not deadlock

- **WHEN** a mutation flow already holds the repo mutation lock
- **AND** an internal helper would acquire the same lock again
- **THEN** the helper uses verified lock provenance or refuses safely
- **AND** it MUST NOT wait on its own lock indefinitely

### Requirement: Lock Failures Fail Closed Without Automation

系统 MUST fail closed before repository mutation on lock conflict, unavailable
lock storage, owner-token mismatch, ambiguous stale lock ownership, and lock
acquisition exceptions.

The system MUST NOT wait indefinitely, auto-retry, repair state, delete
worktrees, prune, commit, merge, push, create branches, create PRs, schedule
background work, invoke runtime subagents, send notifications, or use connectors
as part of lock handling.

Verification lock handling MUST NOT introduce queues, background execution,
additional shell syntax, retry semantics, or new public response fields.

#### Scenario: Lock storage unavailable blocks mutation

- **WHEN** the lock store cannot prove exclusive ownership
- **THEN** the mutation flow is refused
- **AND** no patch, worktree, Git metadata, or repository file mutation occurs

#### Scenario: Suspected stale lock is a safe refusal

- **WHEN** the lock store reports an ambiguous or suspected stale owner
- **THEN** the mutation flow is refused before repository mutation
- **AND** the answer and audit summary MUST NOT expose owner internals, lock paths, DB paths, process details, or manual deletion instructions
- **AND** the system MUST NOT steal, reclaim, override, or delete the lock

#### Scenario: Verification conflict is refused without queueing

- **WHEN** a whitelisted verification request targets a repo whose mutation lock is held
- **THEN** the verification request is safely refused
- **AND** it MUST NOT enqueue, retry, run in the background, or execute shell text

### Requirement: Read-Only Routes Remain Unlocked

系统 SHALL NOT acquire the repo mutation lock for read-only routes unless they
are part of a mutation transaction that must finalize lifecycle state.

Read-only inventory, inspection, audit recovery, capability status, memory/task
status, and repo search MUST continue to avoid repository mutation and MUST NOT
become blocked merely because another RepoPilot mutation lock is held.

#### Scenario: Inventory works during a lock conflict

- **WHEN** a repo mutation lock is held by another mutation flow
- **AND** the user asks for scoped worktree inventory
- **THEN** the inventory route remains read-only
- **AND** it does not attempt to acquire the mutation lock

### Requirement: Lock Audit And Public Output Are Redacted

系统 SHALL keep recognized lock attempts, conflicts, unavailable lock storage,
and release failures auditable through scoped redacted summaries when audit
storage is available.

Audit and public output MAY include safe operation names, lock outcome,
confirmation status, and safe error class. They MUST NOT include local absolute
paths, `.git` paths, DB paths, lock file paths, raw Git output, raw SQLite
errors, raw exception text, patch body, full diff, file content, environment
variables, secrets, process internals, or unknown directory names.

The public `/chat` response schema MUST remain unchanged.

#### Scenario: Lock conflict does not leak storage details

- **WHEN** a mutation request is refused because the repo mutation lock is held
- **THEN** the answer and audit summary may say that a repo mutation is already
  in progress
- **AND** they MUST NOT expose lock storage paths, owner internals, raw
  exceptions, DB paths, or local absolute paths

#### Scenario: Release failure is reported truthfully

- **WHEN** a mutation outcome is already known but releasing the repo mutation lock fails
- **THEN** the answer and audit summary MUST NOT claim the lock was cleanly released
- **AND** they MUST report only safe release-failure status without exposing lock storage paths, owner internals, raw exceptions, DB paths, or local absolute paths
