## Why

`app/worktrees/git_metadata.py` is the shared Git metadata runner used by
worktree inspection, disposal/reconciliation preflight, re-verification, and
verified patch promotion. It already uses fixed argv, `shell=False`,
`GIT_OPTIONAL_LOCKS=0`, a timeout, and a byte limit, but stdout is currently
written to a temporary file until the Git process exits. The size check happens
after `process.wait()`, so an oversized metadata command can write beyond the
intended cap before RepoPilot rejects it.

This stage closes that read-path debt without changing destructive disposal
mutation, public `/chat` shape, provider runtime, live eval, or default CI.

## What Changes

- Replace temporary-file metadata capture with a bounded stdout pipe reader that
  enforces `MAX_GIT_METADATA_BYTES = 256_000` before content is retained or
  decoded.
- Kill and reap the Git process on timeout, oversized stdout, reader failure, or
  reader non-completion, then safely return `None`.
- Preserve the existing public contract:
  - `run_git_metadata(...) -> bytes | None`
  - `git_metadata_text(...) -> str | None`
  - `registry_entries(...) -> dict[str, GitRegistryEntry] | None`
- Preserve fixed argv, `shell=False`, `GIT_OPTIONAL_LOCKS=0`, stderr discarded,
  no raw Git output in public/audit data, no retry, and no repair.
- Add focused tests proving timeout, oversize, non-zero exit, and read failure
  fail closed and do not expose output.
- Update only durable docs whose owned facts change.

Non-goals:

- Do not change `app/worktrees/disposal.py` destructive `_run_mutation()` in this
  stage; its subprocess output cap remains a separate small debt.
- Do not change inspection streaming Git diff handling; that has its own
  timeout-bounded path.
- Do not modify `/chat` public contract, provider runtime, live eval profile,
  default CI, branch/PR automation, commit/merge/push automation, background
  tasks, runtime subagents, connectors, notifications, or `git worktree prune`.

## Capabilities

### Modified Capabilities

- `worktree-inspection`
- `worktree-disposal-reconciliation`
- `worktree-reverification`
- `verified-patch-promotion`

## Impact

- Code:
  - `app/worktrees/git_metadata.py`
- Tests:
  - `tests/test_worktree_disposal.py`
- Docs:
  - `.harness/allowed_files.md`
  - `.harness/review_checklist.md`
  - `docs/PROGRESS.md`
  - `HANDOFF_TO_NEXT_CHAT.md`
  - `openspec/specs/worktree-inspection/spec.md` at archive time
  - `openspec/specs/worktree-disposal-reconciliation/spec.md` at archive time
  - `openspec/specs/worktree-reverification/spec.md` at archive time
  - `openspec/specs/verified-patch-promotion/spec.md` at archive time
