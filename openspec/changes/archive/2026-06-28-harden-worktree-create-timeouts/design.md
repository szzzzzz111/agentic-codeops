## Overview

This stage closes the worktree create / rollback subprocess timeout debt. The intended implementation is small:
keep `WorktreeManager.create()` and its lifecycle semantics intact, but route all local Git subprocesses in
`manager.py` through a bounded helper with one fixed timeout and output hard caps.

## Risk

Risk level is `high` because this touches Git subprocess execution in a write-risk patch/worktree lifecycle path.
The change should reduce process-hang and output-growth risk without widening write authority.

## Current Behavior

`manager.py` currently uses fixed argv and `shell=False`, but the local helpers call `subprocess.run(...,
capture_output=True, text=True)` without timeout or byte caps. Affected paths include:

- repository preflight: `_is_git_repo()`, `_is_bare_repo()`, `_is_git_work_tree()`, `rev-parse HEAD`,
  `_is_repopilot_ignored()`, and `_workspace_status()`;
- worktree creation: `git worktree add --detach --lock ...`;
- rollback: `git worktree unlock`, `git worktree remove --force`, followed by local directory cleanup.

## Proposed Design

Add a manager-local bounded Git helper, for example `_run_git(...)`, that:

- builds only fixed argv as `["git", *args]`;
- sets `cwd` to the already resolved repo path;
- sets `shell=False`;
- sets `GIT_OPTIONAL_LOCKS=0`;
- enforces `WORKTREE_GIT_TIMEOUT_SECONDS = 10.0`;
- captures stdout/stderr only through byte-bounded pipes, not unbounded `capture_output=True`;
- decodes bounded stdout/stderr with `utf-8` replacement for internal checks only;
- enforces `WORKTREE_GIT_OUTPUT_MAX_BYTES = 256_000` independently for stdout and stderr, matching the existing
  inspection metadata cap scale while keeping normal Git metadata/preflight output comfortably below the limit;
- raises `subprocess.SubprocessError` or a local subprocess exception for timeout, oversize, non-zero exit, or
  process start/read failures.

Callers should preserve current public behavior:

- commands whose non-zero exit is business data must opt out of `check=True`; specifically `git check-ignore`
  should return its bounded `CompletedProcess` so `_is_repopilot_ignored()` can distinguish `returncode == 0`
  (ignored), `returncode == 1` (not ignored -> `repopilot_not_ignored`), and `returncode > 1` or
  timeout/oversize/process failure (safe `create_failed`) without exposing raw output;
- preflight failures return the existing safe reasons such as `not_git_repo`, `bare_repo`, `not_git_worktree`,
  `missing_head`, `repopilot_not_ignored`, or `workspace_not_clean`;
- create failures return `create_failed` and leave the patch pending;
- rollback remains best-effort, suppressing subprocess failures after attempting bounded unlock/remove;
- no raw Git output or exception text enters public summary, tool calls, or persistent audit.

For output bounding, use a Windows-safe dual-pipe mechanism such as one capped reader thread per pipe. The helper
should start both readers, wait for process completion within the deadline, kill/reap on timeout, then join the readers
with short bounded waits. If either reader reports more than `WORKTREE_GIT_OUTPUT_MAX_BYTES = 256_000`, kill/reap the
process and fail closed. Do not use `select()` for Windows pipe readiness, and do not use `communicate()` in a way that
can buffer unlimited output before the cap is checked.

## Non-Goals

- No change to worktree ids, path layout, lifecycle states, patch states, repo mutation lock behavior, or routing.
- No change to `/chat` top-level fields or public command syntax.
- No `git worktree prune`, automatic retry, automatic repair, commit, merge, push, branch/PR automation, background
  worker, runtime subagent, connector, or notification.
- No broad subprocess hardening outside `app/worktrees/manager.py`.

## Test Strategy

Use TDD after approval:

- Add RED tests proving `_git` / `_git_stdout` timeout returns safe create failure and does not expose raw command
  output.
- Add RED tests proving stdout or stderr oversize is killed/reaped and returns safe create failure.
- Add RED tests preserving `check-ignore` business semantics: a bounded non-zero exit still maps to
  `repopilot_not_ignored` only for return code 1; return code greater than 1, timeout, and oversize map to safe
  `create_failed`.
- Add RED tests proving rollback uses bounded unlock/remove and does not hang or propagate raw exceptions when metadata
  persistence fails.
- Add an explicit negative assertion that rollback timeout/failure cannot convert an unsafe partial create into
  `created=True`.
- Add tests by monkeypatching timeout/output cap constants to small values so timeout and stdout/stderr oversize are
  deterministic and fast.
- Preserve existing success and failure behavior: clean repo creation, dirty workspace rejection, ignored file allowance,
  metadata persistence rollback, id collision protection, non-git/bare/no-HEAD/repopilot-not-ignored failures, and
  AgentLoop patch-in-worktree flow.
- Run focused `pytest tests/test_worktree_isolation.py -q`, adjacent worktree/AgentLoop/API tests, full
  `scripts/verify.ps1`, OpenSpec validation, and `git diff --check`.

## Review Plan

Before implementation, complete:

- internal plan review;
- Codex independent plan review;
- OpenCode independent plan review, after `opencode session list` and reusing an existing relevant session.

All findings must be classified as `fix`, `clarify`, `reject`, or `defer` before implementation starts.
