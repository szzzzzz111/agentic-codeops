## Current Behavior

V20 creates detached locked worktrees under `.repopilot/worktrees/<worktree_id>`. V21 inspects scoped retained worktrees without mutation. V22 re-verifies eligible retained worktrees after fail-closed consistency preflight. No current runtime path disposes or reconciles a retained worktree.

V21/V22 Git metadata helpers have no independent timeout and some output limits are enforced only after process capture/read. The patch-store existing lookup also creates state, and its legacy `mark_status(patch_id, status)` is not scope-qualified.

## Commands, Confirmation, And Routing

V23 accepts only complete normalized matches:

- `confirm discard worktree <worktree_id>`
- `确认丢弃 worktree <worktree_id>`
- `confirm reconcile worktree <worktree_id>`
- `确认协调 worktree <worktree_id>`

The `confirm` prefix is mandatory because V23 performs irreversible directory/registry removal and writes worktree/patch terminal states. V22 re-verification is repeatable, does not delete retained state, and therefore keeps its existing non-confirm-prefixed command.

The parser uses:

- start-anchored command-like intent detection for only `discard worktree`, `reconcile worktree`, and their optional confirmed forms;
- full-match execution patterns that require `confirm`/`确认`, one safe worktree id, and no extra text.

Discussion such as `how to discard changes` or `how to discard worktree changes` does not begin with a supported command phrase and MUST NOT match. A disposal-like command missing confirmation is recognized and rejected as a whole, so it cannot fall through.

AgentLoop order is inventory/inspection, V23 disposal/reconciliation, V22 re-verification, patch handling, standalone verification, audit recovery, and fallback. V23 precedes V22 because disposal is a terminal destructive lifecycle action whose malformed attempts must be intercepted before any later execution route, and disposed worktrees must not re-enter re-verification. Exact V23 and V22 command shapes do not conflict.

## Shared Git Metadata Runner Is Blocking

V23 destructive decisions depend on trusted registry, lock, linked-worktree ownership, and HEAD metadata. Therefore V23 MUST first replace V21/V22 metadata subprocess helpers with a shared runner that uses fixed argv, `shell=False`, `GIT_OPTIONAL_LOCKS=0`, an independent timeout, and a bounded temporary output sink. The runner checks output byte size before reading content and fails closed on timeout, oversize, non-zero exit, malformed data, or exception. It never retries automatically.

This work is blocking rather than cleanup because deletion cannot safely depend on the known unbounded metadata path. V21 inspection and V22 re-verification migrate to the shared runner in the same implementation stage and receive regression coverage.

## Scoped Metadata And Trusted Identity

Worktree metadata is loaded only from the current `user_id + repo_key` store. Unknown, cross-user, and cross-repo ids return the same safe not-found result before Git or filesystem mutation.

The expected path is reconstructed only from resolved request repo root, fixed `.repopilot/worktrees` managed root, and validated scoped worktree id. Preflight rejects repo root, managed root, paths outside managed root, symlinks/reparse points, malformed metadata, and the main worktree.

Linked-worktree ownership attestation is exact and internal:

- the expected directory `.git` entry MUST be a regular non-symlink file;
- fixed metadata reads inside the expected directory MUST report `--is-inside-work-tree=true`, `--show-toplevel` equal to the expected directory, and `--git-common-dir` equal to the original repo common Git directory;
- the `.git` file target MUST resolve under that common Git directory's `worktrees/` administrative root;
- the linked-worktree administrative `gitdir` back-reference MUST resolve exactly to the expected directory `.git` file.

When the registry entry is missing but the expected directory exists, reconciliation may delete it only after this ownership attestation and `HEAD == base_commit` both pass. Merely matching expected path and HEAD is insufficient proof. Registry absence is accepted only from a successfully parsed complete registry result; unavailable or malformed registry metadata fails closed.

Before any destructive command, the associated patch MUST be found through the true no-create patch-store lookup in the same `user_id + repo_key` scope. Normal disposal and residual reconciliation require patch status `applied_in_worktree`; complete idempotent or patch-only closeout may accept patch status `discarded`. Missing, cross-scope, or other-status patches fail before destructive mutation.

## Preflight Classification

Normal discard accepts only `patch_applied`, `verification_failed`, or `verification_succeeded` with directory present, exact registry path, valid linked-worktree ownership, and matching HEAD/base.

Reconciliation is a narrow disposal finisher:

| Observed state | Allowed reconciliation |
|---|---|
| directory and registry both missing | metadata-only closeout |
| directory missing, exact registry entry present | unlock only when registry says locked, then remove exact entry |
| registry missing, directory present | delete only after ownership and HEAD/base attestation |
| directory and registry present after earlier unlock | skip unlock and continue exact remove |
| worktree `discarded`, scoped patch not `discarded` | patch-only closeout |

Path mismatch, HEAD/base mismatch, damaged/unknown metadata, cross scope, unknown ids, main worktree, managed root, unknown directory ownership, and unsupported lifecycle always fail closed. V23 never runs `git worktree prune`.

## Execution Order And Results

Accepted disposal passes through `ToolRegistry -> PermissionPolicy -> ApprovalGate -> ToolExecutor.worktree_dispose`.

Normal execution order is:

1. scoped preflight;
2. unlock only when the exact registry record is locked;
3. fixed-argv `git worktree remove --force`;
4. confirm exact registry entry and expected directory are absent;
5. update scoped worktree to `discarded`;
6. update scoped associated patch to `discarded`;
7. return safe result and attempt persistent audit.

Reconciliation skips only steps already proven complete. Any step failure stops immediately with no retry and no rollback of completed destructive steps.

## Lifecycle Transition Table

| Current worktree state | Request and condition | Worktree result | Patch result |
|---|---|---|---|
| `patch_applied` / `verification_failed` / `verification_succeeded` | confirmed discard completes | `discarded` | `discarded` |
| eligible retained state | failure before mutation | unchanged | unchanged |
| eligible retained state | any unlock/remove command attempted or post-check fails | `disposal_failed` when writable | unchanged |
| eligible retained state | cleanup confirmed but worktree update fails | existing DB value remains | unchanged |
| `disposal_failed` | confirmed reconcile in safe residual set completes | `discarded` | `discarded` |
| `disposal_failed` | confirmed discard | rejected | unchanged |
| `discarded` | patch not discarded and confirmed reconcile | `discarded` | `discarded` |
| `discarded` | patch already discarded and discard/reconcile repeats | `discarded`, idempotent success | `discarded` |
| `ready` / `create_failed` / `patch_failed` / unknown | any V23 request | rejected | unchanged |

If patch update fails after worktree metadata is `discarded`, the worktree remains `discarded`; a later confirmed reconciliation may perform patch-only closeout.

## Patch Store Interfaces

V23 adds `SQLitePatchStore.for_existing_repo(...)`, which returns `None` when the patch DB is absent and never creates `.repopilot` or the DB. V23 also adds `mark_status_scoped(patch_id, *, user_id, repo_key, status) -> bool`, whose SQL qualifies all three identity fields and reports whether a row changed.

V23 uses only `mark_status_scoped`. The legacy `mark_status(patch_id, status)` remains unchanged for compatibility with V16-V22; migrating or removing it is outside V23.

## Audit And Public Contract

Every recognized attempt tries to persist one scoped `worktree_disposal` event related to the requested worktree id. Safe fields include `attempt_kind=discard|reconcile`, confirmation, preflight classification, completed step, failed step, and safe worktree/patch terminal states.

Answers, trace, tool calls, and audit MUST NOT contain absolute paths, raw Git output, DB paths, environment variables, secrets, diff, patch body, or unknown directory names. `related_files` remains empty. `/chat` top-level fields remain `trace_id`, `answer`, `related_files`, and `tool_calls`.

## Non-Goals

V23 does not promote, reapply, or modify patches; commit, merge, or push; repair path/HEAD/metadata mismatches; implicitly reconcile; automatically retry; run arbitrary shell; use `git worktree prune`; call repo RAG or verification; add public APIs/fields; or add background tasks, subagents, connectors, or frontend behavior.
