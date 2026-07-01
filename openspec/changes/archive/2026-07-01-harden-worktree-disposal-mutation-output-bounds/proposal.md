## Why

`app/worktrees/disposal.py::_run_mutation()` executes destructive Git worktree
mutation commands for confirmed disposal/reconciliation. It already uses fixed
argv, `shell=False`, `GIT_OPTIONAL_LOCKS=0`, `check=True`, and a timeout, but it
still relies on `subprocess.run(..., capture_output=True)`.

That means stdout/stderr are captured by Python before RepoPilot can enforce a
read-before-retention hard cap. The prior Git metadata stage closed the shared
read-only/preflight metadata runner; this stage closes the remaining
destructive mutation subprocess output-bound debt without changing disposal
eligibility, lifecycle, public `/chat` shape, provider runtime, live eval, or
default CI.

## What Changes

- Replace `_run_mutation()` use of `capture_output=True` with a disposal-local
  bounded subprocess runner for Git mutation commands.
- Preserve fixed argv, `shell=False`, `GIT_OPTIONAL_LOCKS=0`, existing command
  order, timeout behavior, no retry, no repair, and no raw stdout/stderr
  exposure.
- Enforce independent stdout and stderr hard caps before captured bytes are
  retained or decoded.
- Kill and bounded-reap an already-started Git process on timeout, oversized
  stdout/stderr, read failure, reader non-completion, or non-zero exit; fail
  safely if the process cannot be started.
- Preserve existing disposal failure semantics: unlock/remove mutation failures
  stop immediately, may mark the scoped worktree `disposal_failed`, and preserve
  the patch as `applied_in_worktree`.
- Add focused RED tests for timeout, output oversize, read failure, non-zero
  exit, and unchanged lifecycle behavior.
- Update only durable docs whose owned facts changed.

Non-goals:

- Do not change disposal preflight, ownership checks, registry parsing,
  metadata runner, postcheck semantics, reconciliation eligibility, audit schema,
  repo mutation locking, `ToolExecutor`, `PermissionPolicy`, `ApprovalGate`, or
  `/chat` public contract.
- Do not modify worktree create, inspection streaming diff, re-verification,
  promotion, provider runtime, live eval profile, default CI, branch/PR
  automation, commit/merge/push automation, background tasks, runtime subagents,
  connectors, notifications, or `git worktree prune`.

## Capabilities

### Modified Capabilities

- `worktree-disposal-reconciliation`

## Impact

- Code:
  - `app/worktrees/disposal.py`
- Tests:
  - `tests/test_worktree_disposal.py`
- Docs:
  - `.harness/allowed_files.md`
  - `.harness/review_checklist.md`
  - `docs/PROGRESS.md`
  - `HANDOFF_TO_NEXT_CHAT.md`
  - `openspec/specs/worktree-disposal-reconciliation/spec.md` at archive time
