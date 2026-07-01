## Context

Disposal and reconciliation have two Git subprocess families:

- read-only/preflight metadata reads through the shared hardened metadata
  runner; and
- destructive mutation commands through `app/worktrees/disposal.py::_run_mutation()`.

The first family is already pre-read bounded. The second family still uses
`subprocess.run(..., capture_output=True, timeout=20)`. This stage hardens only
the second family.

## Risk

Risk level: `high`.

Reason: `_run_mutation()` runs destructive Git worktree commands after
eligibility and ownership preflight. A subprocess output or timeout bug here can
affect disposal/reconciliation lifecycle truthfulness and process safety.

## Target Behavior

`_run_mutation(cwd, *args)` shall:

- construct only `["git", *args]`;
- use `shell=False`;
- set `GIT_OPTIONAL_LOCKS=0`;
- start stdout and stderr as pipes;
- read stdout and stderr with Windows-safe bounded background readers;
- enforce independent output caps before bytes are retained, decoded, logged, or
  exposed;
- use `WORKTREE_DISPOSAL_MUTATION_TIMEOUT_SECONDS = 20.0`;
- use `WORKTREE_DISPOSAL_MUTATION_OUTPUT_MAX_BYTES = 256_000` independently for
  stdout and stderr;
- use `WORKTREE_DISPOSAL_MUTATION_REAP_TIMEOUT_SECONDS = 1.0` for post-kill
  reaping;
- use `WORKTREE_DISPOSAL_MUTATION_READER_JOIN_TIMEOUT_SECONDS = 1.0` when waiting
  for output readers after process exit or kill;
- kill and bounded-reap an already-started process on timeout, stdout/stderr
  oversize, reader failure, reader non-completion, or non-zero exit;
- fail safely if the process cannot be started;
- raise only a safe generic failure to the disposal caller;
- never retry, repair, mutate command arguments, expose raw output, or include
  local absolute paths in public/audit data.

The readers may transiently read one byte beyond the cap only to detect oversize
output, but cap-exceeding content must not be retained, decoded, logged, or
returned.

## Failure Semantics

- Timeout: kill, bounded reap, raise safe mutation failure.
- Oversized stdout/stderr: kill, bounded reap, raise safe mutation failure.
- Reader failure or reader non-completion: kill, bounded reap, raise safe
  mutation failure.
- Process start failure: raise safe mutation failure.
- Non-zero exit: complete bounded reader cleanup/reap, raise safe mutation
  failure.

The safe mutation failure type MUST be caught by the existing disposal caller's
`except (OSError, RuntimeError, subprocess.SubprocessError)` boundary. The
bounded helper SHOULD raise `subprocess.SubprocessError` for subprocess safety
failures unless an underlying `OSError` is raised before process start.

Existing disposal semantics continue to apply:

- preflight failures occur before mutation and do not mark terminal state;
- unlock/remove failure stops immediately;
- mutation-after-start failures may set the scoped worktree to
  `disposal_failed`;
- patch state remains `applied_in_worktree` until confirmed terminal closeout;
- no automatic retry, rollback of completed destructive steps, repair, prune, or
  cleanup outside the current ordered flow.

## Non-Goals

- No changes to `_preflight()`, `_ownership_matches()`, `registry_entries()`,
  `git_metadata_text()`, shared metadata runner, postcheck logic, audit schema,
  repo mutation lock, ToolExecutor, PermissionPolicy, ApprovalGate, or public
  `/chat` schema.
- No changes to worktree create, inspection, re-verification, promotion,
  verification runner, patch apply, provider runtime, live eval, default CI, or
  branch/PR/commit/merge/push automation.
- No `git worktree prune`.

## Test Plan

- RED tests for `_run_mutation()` timeout proving the process is killed and
  bounded-reaped without retry.
- RED tests for stdout and stderr oversize proving the process is killed/reaped
  before a normally-blocking fake process exits and raw output is not surfaced.
- RED tests for stdout/stderr read failure or reader non-completion returning a
  safe mutation failure.
- Regression tests for process start failure and non-zero exit.
- Regression tests for mutation failures whose raw output, stderr, exception
  text, traceback-like text, local absolute paths, DB paths, or patch/diff-like
  content must not appear in `WorktreeDisposalResult.public_summary`,
  AgentLoop public output, or worktree disposal audit records.
- Regression coverage proving disposal still records unlock/remove mutation
  failure as `mutation_failed`, sets `disposal_failed` when mutation was
  attempted, and preserves the patch as `applied_in_worktree`.
- Verification:
  - focused `pytest tests/test_worktree_disposal.py -q`;
  - adjacent worktree disposal/reconciliation and mutation-locking tests;
  - `ruff check .`;
  - `openspec validate --all`;
  - `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`;
  - `git diff --check`.

## Review Plan

Because this is high risk, complete before implementation:

- internal plan review;
- Codex independent plan review;
- OpenCode independent plan review, first running `opencode session list` and
  then reusing an existing review session when available.

All plan and implementation findings must be classified as `fix`, `clarify`,
`reject`, or `defer`.
