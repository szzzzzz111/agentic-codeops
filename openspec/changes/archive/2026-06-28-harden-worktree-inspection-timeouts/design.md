## Overview

This stage closes the read-only worktree inspection streaming timeout debt. The intended implementation is small:
keep the current inspection flow, but replace unbounded streaming subprocess handling with a helper that applies one
fixed deadline across stdout consumption and process finalization.

## Current Behavior

`inspection.py` already uses `run_git_metadata()` for metadata commands such as `rev-parse`,
`diff --name-only -z`, `diff --numstat -z`, and `status --porcelain -z`. Those calls have a timeout and output cap.

Two streaming paths remain weaker:

- `_stream_hunk_count()` runs `git diff --unified=0 ...` with `_popen_git()`, reads stdout line by line, then calls
  `process.wait()` without timeout.
- `_format_preview()` runs per-file `git diff ... -- <path>`, reads bounded lines, then calls `process.wait()`
  without timeout.

## Proposed Design

Add a small inspection-local helper, for example a callback-style
`_consume_streaming_git(cwd, *args, on_line=...)`, that:

- starts fixed-argv Git with `shell=False` and `GIT_OPTIONAL_LOCKS=0`;
- consumes stdout through the existing bounded line limits without trusting stderr;
- enforces `INSPECTION_STREAM_TIMEOUT_SECONDS` across both reading and `process.wait()`;
- returns structured status such as `(success, partial)` while callers keep their own counters/output;
- on timeout, blocked read, or `TimeoutExpired`, kills and reaps the process, then returns `success=False`;
- on `OSError` or other `subprocess.SubprocessError`, returns `False`;
- never exposes exception text or stderr.

The implementation mechanism must work on Windows. A blocking `stdout.readline()` cannot be protected by
`process.wait(timeout=...)` alone. Use a cross-platform approach such as a watchdog timer/thread that kills and reaps
the process when the deadline expires, then lets the bounded reader terminate safely. Do not switch to
`communicate(timeout=...)` if doing so would buffer unbounded raw diff output.

Use the helper in both `_stream_hunk_count()` and `_format_preview()`. Existing preview bounds, redaction, and unsafe
path omission stay in place; the helper closes the read/wait timeout gap. If a timeout occurs:

- hunk count returns the count collected so far with `partial=True`;
- preview omits the affected file, marks `partial=True`, and does not add raw or partial untrusted output for that
  file to the public preview.

## Test Strategy

Use TDD after implementation approval:

- Add RED tests with fake streaming processes that trigger timeout before clean EOF/finalization.
- Assert hunk count and preview return safe partial results, call `kill()`, and do not expose raw path/exception text.
- Preserve or adapt the existing Git start-failure regression, and add coverage for non-zero exit / subprocess failure
  if the helper refactor changes that behavior surface.
- Add a success-path regression proving existing preview and hunk count behavior still works.
- Run focused `pytest tests/test_worktree_inspection.py -q`, adjacent worktree/AgentLoop/API tests if needed, full
  `scripts/verify.ps1`, OpenSpec validation, and `git diff --check`.

## Review Plan

Risk is `high` because this touches Git/subprocess process handling. Before implementation, complete:

- internal plan review;
- Codex independent plan review;
- OpenCode independent plan review, reusing an existing review session when possible.

All findings must be triaged as `fix`, `clarify`, `reject`, or `defer` before implementation starts.
