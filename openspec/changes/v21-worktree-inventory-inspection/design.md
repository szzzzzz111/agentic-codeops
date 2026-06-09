## Current Behavior

V20 persists worktree metadata in `.repopilot/worktrees.sqlite3`, scoped by `user_id + repo_key`, and supports only a narrow per-id status answer. The current status route emits `worktree_status`, which normally causes the unified `AgentLoop.run()` audit wrapper to persist a trace/worktree event.

## Target Behavior

V21 adds:

- Inventory: list the latest 20 metadata records in the current scope, ordered by `created_at DESC, worktree_id DESC`.
- Inspection: upgrade the existing status commands to return metadata, tracked Git changes, consistency results, and bounded preview.
- Strict read semantics: no `.repopilot/` or DB creation, no state repair, no repository mutation, no persistent audit write.

V21 inspection replaces the V20 narrow status behavior. The route emits `worktree_inspection`; inventory emits `worktree_inventory`. The old `worktree_status` trace event is not retained as a parallel route.

## Internal Interfaces

`SQLiteWorktreeStore.list_worktrees(user_id, repo_key, limit=20)` returns scoped `WorktreeRecord` values through a read-only SQLite connection.

`WorktreeManager.inventory(repo_path, user_id)` returns a safe inventory result containing records or an empty/missing-store result.

`WorktreeManager.inspect(repo_path, user_id, worktree_id)` returns an internal inspection result with:

- metadata presence and safe metadata fields,
- `directory_present`,
- `git_registry_present`,
- `registry_path_matches_expected`,
- `head_matches_base_commit`,
- tracked changed-file paths,
- aggregate additions, deletions, binary-file count, and hunk count,
- untracked count only,
- verification label/status,
- safe preview text and omitted/truncated counters.

The public formatter consumes this internal result and writes only bounded, redacted text into `/chat.answer`.
Metadata scalars and tracked changed-file summaries also pass through bounded public formatting:
control whitespace is collapsed, paths/secrets/state paths are redacted, scalar lengths are capped,
and only the first 20 tracked paths are displayed with an explicit omitted count.

## Git Data Flow

All Git subprocess calls use fixed argv, `shell=False`, `GIT_OPTIONAL_LOCKS=0`, bounded captured output, and the expected worktree directory derived from trusted repo-local metadata. Read-only SQLite connections use `mode=ro&immutable=1`.

Preview paths MUST NOT come from the user message, persisted `changed_files`, or human-readable `--stat` output.

1. Resolve the scoped metadata record without creating state.
2. Parse `git worktree list --porcelain -z` to check registry consistency.
3. If the expected directory and scoped record are usable, obtain tracked paths only from:
   - `git diff --name-only -z --no-ext-diff --no-textconv <base_commit> --`
4. Obtain machine-readable diffstat only from:
   - `git diff --numstat -z --no-ext-diff --no-textconv <base_commit> --`
5. Count hunks by streaming fixed-argv `git diff --unified=0 --no-ext-diff --no-textconv <base_commit> --` output and counting hunk headers without retaining patch bodies.
6. Count untracked files from fixed status output, but never expose their names or content.
7. For each Git-derived tracked path that passes safe-file validation, stream a per-file preview with:
   - `git diff --no-ext-diff --no-textconv <base_commit> -- <git-derived-path>`

The Git reader MUST drain streamed output while retaining only counters and the configured preview budget. It MUST NOT use unbounded `capture_output=True` for patch-body or aggregate hunk-count commands. Name-only, numstat, registry, and status metadata commands remain bounded by explicit output caps; exceeding a cap produces a safe partial/unavailable finding.

Git errors and missing/inconsistent state become safe consistency findings. V21 never repairs them.

## Bounded Safe Preview

A dedicated formatter owns preview validation, redaction, and budgeting. Public or persistent structures MUST NOT use `diff`, `diff_text`, or `full_diff` fields.

Fixed limits:

- maximum files: 20,
- maximum total characters: 6000,
- maximum lines per file: 80,
- maximum characters per line: 300.

The formatter rejects binary files, sensitive names/extensions, hidden path components, `.git/**`, and `.repopilot/**`. It redacts local absolute paths, DB paths, common secret/credential assignments, and reports omitted/truncated file, line, and character counts.

Raw Git diff output is consumed line-by-line only while formatting the current inspection answer. Only bounded redacted preview text and counters are retained; raw output never enters internal trace summaries, tool calls, return dataclasses intended for persistence, or persistent audit.

## Audit And Traceability

`AgentLoop.run() -> _run_inner() -> _record_audit_and_return()` remains the uniform request structure.

`_skip_persistent_audit_for_result()` MUST return true when a result contains either `worktree_inventory` or `worktree_inspection`. This preserves internal request-local traceability while ensuring strict read requests do not create or update `audit.sqlite3`.

Closeout evidence MUST prove:

- an existing audit DB receives no new rows after inventory / inspection,
- a missing audit DB and missing worktree DB remain missing,
- preview text never appears in persistent audit or trace summaries.

## Error Behavior

- Missing store or empty scope: return an empty inventory answer without state creation.
- Unknown/cross-scope id: return not-found without Git inspection.
- Missing directory, missing registry entry, path mismatch, or HEAD mismatch: return explicit safe consistency findings.
- Git command failure: return a safe inspection-unavailable or partial-result finding without stdout/stderr leakage.
- Unsafe or binary tracked path: omit preview for that file and increment omitted counters.

## Non-Goals

V21 does not run verification, clean up or repair worktrees, discard, unlock/remove, reconcile state, promote patches, modify the main workspace, commit, merge, push, run background jobs, schedule subagents, use connectors, or add frontend/API surfaces.
