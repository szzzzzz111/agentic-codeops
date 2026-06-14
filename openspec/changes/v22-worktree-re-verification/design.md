## Current Behavior

V20 retains detached, locked worktrees and records their scoped metadata and lifecycle. Combined Patch + Verify can verify during initial patch execution. V21 can inspect retained worktrees but is strictly read-only. Standalone verification runs against the request repo path.

## Target Behavior

V22 recognizes only:

- `worktree verify <worktree_id> <command_label>`
- `重新验证 worktree <worktree_id> <command_label>`

The full normalized message MUST match one of these shapes. The label MUST normalize through the existing `pytest`, `ruff`, or `verify` whitelist. Extra arguments, paths, environment variables, pipes, redirection, shell syntax, unknown labels, and partial matches are rejected before any Git or verification execution.

Routing MUST first recognize the bounded re-verification command prefix, then either accept the exact safe shape or return a V22 rejection. Unsafe or malformed re-verification-like requests MUST NOT fall through to standalone verification, patch handling, audit recovery, capability status, or repo-search fallback.

## Recommended Architecture

Add a focused worktree re-verification parser and orchestration path. The AgentLoop handles this intent immediately after `_run_worktree_inventory` / `_run_worktree_inspection` routing and before `_run_patch_verify_loop`, patch handling, standalone verification, audit recovery, capability status, and repo-search fallback.

`WorktreeManager.prepare_reverification(...)` returns an internal preflight result containing:

- `accepted`
- safe failure reason
- scoped `WorktreeRecord` when found
- trusted internal `execution_repo_path` only when all checks pass

The internal execution path is not stored in SQLite. Preflight MUST reconstruct it from the resolved request repo root, the fixed `.repopilot/worktrees` managed root, and the scoped validated `worktree_id`. It MUST NOT enter public answers, trace summaries, tool-call parameters, `ToolInvocationContext`, SQLite metadata, or persistent audit.

## Fail-Closed Preflight

Preflight is narrower than V21 full inspection and MUST NOT collect diff, preview, diffstat, hunk count, or untracked data.

1. Open the existing worktree store without creating state.
2. Resolve the worktree record by current `user_id + repo_key`; unknown and cross-scope ids return the same safe not-found result.
3. Require worktree lifecycle to be `patch_applied`, `verification_failed`, or `verification_succeeded`; reject `ready`, `create_failed`, `patch_failed`, and unknown states before Git inspection.
4. Derive the expected directory only from trusted repo root plus `.repopilot/worktrees/<worktree_id>`.
5. Verify the expected directory exists.
6. Parse fixed-argv `git worktree list --porcelain -z` from the original repo.
7. Verify registry membership and exact normalized registry-path equality.
8. Run fixed-argv `git rev-parse HEAD` inside the expected directory and require equality with metadata `base_commit`.

Any missing, inconsistent, malformed, unavailable, or exceptional condition fails closed. The system MUST NOT run verification, repair metadata, reconcile state, cleanup, unlock/remove, retry Git, create an unknown worktree, or modify the main workspace.

Because verification did not execute, preflight failure preserves the previous worktree lifecycle and verification summary.

## Verification Execution

After successful preflight, AgentLoop builds a normalized verification context and reuses:

`ToolRegistry -> PermissionPolicy -> ApprovalGate -> ToolExecutor.verification_run(execution_repo_path, command_label)`

The existing fixed whitelist, argv lists, `shell=False`, timeout, stdout/stderr excerpt limits, answer limit, and redaction remain authoritative. V22 does not add labels or accept user-controlled argv, cwd, path, environment, or timeout.

Execution outcomes update existing worktree fields:

- Verification Runner `success` -> lifecycle `verification_succeeded`
- `failed`, `timed_out`, `unavailable`, runner exception, or other non-success execution result -> lifecycle `verification_failed`

No `verification_rerun_*` lifecycle is added. The related patch store is not read or written by the re-verification flow, so the patch remains `applied_in_worktree` after success, failure, or preflight rejection.

## Attempt And Audit Model

Every recognized re-verification request produces one redacted persistent `verification_result` audit event related to the `worktree_id`. `attempt_kind=worktree_reverification` and `related_id=<worktree_id>` are mandatory for V22 attempt events and distinguish them from standalone verification events.

Safe fields include:

- `attempt_kind=worktree_reverification`
- `worktree_id` as `related_id`
- `command_label` when safely parsed
- `execution_attempted=true/false`
- `preflight_status=passed/failed`
- safe failure reason or verification status
- exit code, duration, timeout, and truncation flags when execution occurred

The count of scoped `verification_result` events with `attempt_kind=worktree_reverification` and the same related worktree id is the rerun count. V22 does not migrate worktree or audit schemas and does not persist a mutable rerun counter.

Audit remains best-effort under the existing V19 rule. The primary `/chat` result is preserved if audit persistence fails, and request-local trace records only a safe `audit_persistence_failed` summary.

## Public Result And Trace

The answer reports a concise safe result containing `worktree_id`, command label, preflight/execution status, and the existing bounded redacted verification summary when execution occurred. Executed answers MUST be visibly distinguishable from standalone verification, for example by beginning with `worktree_id=<id>;` before the verification summary.

`related_files` remains empty. A successful execution may expose one safe `verification_run` tool-call summary, which MUST NOT include cwd or paths. Preflight failures expose no verification tool call.

Trace and persistent audit MUST NOT contain full stdout/stderr, absolute paths, `.git` paths, DB paths, environment variables, secrets, raw Git output, diff, or preview.

## Error Behavior

- Unknown/cross-scope id: safe not-found, no Git inspection, no verification.
- Missing directory, registry entry, path mismatch, or HEAD mismatch: safe preflight failure, no verification, lifecycle unchanged.
- Git exception or malformed output: safe preflight failure, no automatic repair or retry.
- Permission/approval rejection: no verification; record safe failed attempt without changing lifecycle.
- Verification exception/non-success: safe result, lifecycle `verification_failed`, patch unchanged.

## Non-Goals

V22 does not clean up, discard, unlock/remove, reconcile, promote, commit, merge, push, modify/reapply patches, modify the main workspace, add REST APIs or `/chat` fields, add arbitrary shell or labels, run background tasks, schedule subagents, use connectors, or add frontend behavior.
