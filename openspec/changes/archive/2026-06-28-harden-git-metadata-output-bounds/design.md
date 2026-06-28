## Context

`run_git_metadata()` is intentionally shared across read-only or preflight Git
metadata reads. It is used by:

- V21 inspection metadata helpers;
- V23 disposal/reconciliation registry and ownership preflight;
- V22 re-verification preflight;
- V25 promotion preflight through disposal consistency checks and main-workspace
  metadata reads.

The current implementation redirects stdout to a temporary file, waits for the
process, checks `output.tell()`, and then reads at most `max_bytes + 1`. This
prevents unbounded in-memory capture, but it does not enforce the cap before
Git writes to disk, and timeout cleanup calls an unbounded post-kill `wait()`.

## Risk

Risk level: `high`.

Reason: this touches Git subprocess handling used by worktree lifecycle
preflights. The intended file count is small, but fail-open metadata handling
could affect destructive disposal, re-verification, or promotion eligibility.

## Target Behavior

`run_git_metadata(cwd, *args, timeout=10.0, max_bytes=256_000)` shall:

- construct only `["git", *args]`;
- use `shell=False`;
- set `GIT_OPTIONAL_LOCKS=0`;
- discard stderr;
- start stdout as a pipe;
- read stdout in a Windows-safe background reader with a hard cap;
- never retain bytes beyond `max_bytes`;
- kill and reap on timeout, oversized stdout, read failure, reader join timeout,
  process-start failure, or non-zero exit;
- use `GIT_METADATA_REAP_TIMEOUT_SECONDS = 1.0` for post-kill reaping rather
  than an unbounded `wait()`;
- use `GIT_METADATA_READER_JOIN_TIMEOUT_SECONDS = 1.0` when waiting for the
  background stdout reader to finish after process exit or kill;
- return `None` for every unsafe or unavailable outcome;
- return bytes only for successful zero-exit Git commands whose stdout is within
  the cap;
- never retry, repair, mutate metadata, expose raw output, or raise raw
  subprocess exceptions to callers.

The reader may read one byte beyond the cap solely to detect oversize output,
but that extra byte must not be retained.

## Failure Semantics

- Timeout: kill, bounded reap, return `None`.
- Oversize stdout: kill, bounded reap, return `None`.
- Reader failure or non-completion: kill, bounded reap, return `None`.
- Non-zero exit: bounded cleanup, return `None`.
- Invalid UTF-8 in `git_metadata_text()`: return `None`.
- Malformed worktree registry output: existing parsers continue returning
  `None`.

Callers continue to map `None` to their existing safe outcomes:

- inspection partial/unavailable findings;
- disposal/reconciliation preflight failure before mutation;
- disposal/reconciliation post-mutation `registry_entries()` failure remains a
  failed disposal outcome, preserving existing `mutation_failed` /
  `disposal_failed` semantics rather than reporting success;
- re-verification preflight failure before verification execution;
- promotion preflight failure before main-workspace writes.

## Non-Goals

- No changes to destructive disposal `_run_mutation()`; that is a follow-up debt
  with different write-path semantics.
- No changes to worktree create helper, inspection streaming diff helper,
  verification runner, patch apply, promotion state machine, audit schema, or
  `/chat` public schema.
- No new network dependency, provider API key, background worker, runtime
  subagent, connector, notification, branch/PR automation, commit/merge/push
  automation, or `git worktree prune`.

## Test Plan

- RED tests for metadata timeout proving kill and bounded reap are attempted.
- RED tests for stdout oversize proving the process is killed/reaped before a
  normally-blocking fake process exits, and oversized bytes are not returned.
  Include cap-edge assertions: exactly `max_bytes` may succeed, while
  `max_bytes + 1` returns `None`.
- RED assertions should verify the configured bounded post-kill reap timeout is
  used instead of an unbounded post-kill wait.
- RED tests for stdout read failure or reader non-completion returning `None`.
- Regression tests for non-zero exit returning `None`.
- Regression coverage proving disposal postcheck metadata unavailability after
  mutation continues to return a safe failed disposal result rather than success.
- Existing tests for invalid UTF-8, registry parsing, disposal preflight,
  re-verification, promotion, and inspection remain passing.
- Verification:
  - focused `pytest tests/test_worktree_disposal.py -q`;
  - adjacent worktree inspection/reverification/promotion/disposal tests;
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
