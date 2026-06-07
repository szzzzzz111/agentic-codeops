## Current Behavior

- Standalone patch confirm uses `PatchManager.prepare_apply(...)` and then calls `ToolExecutor.patch_apply(repo_path=request.repo_path, diff_text=...)`.
- Combined Patch + Verify first applies the patch to `request.repo_path`, then runs combined verification against the same path.
- Standalone verification also runs against `request.repo_path`.
- Persistent audit stores patch / verification / task summaries, but no worktree lifecycle exists.

## Target Behavior

- Introduce `app/worktrees/` with a repo-local manager and SQLite store at `.repopilot/worktrees.sqlite3`.
- Add an approval-gated `worktree_create` tool that creates a detached, locked Git worktree under `.repopilot/worktrees/<worktree_id>`.
- For standalone patch confirm and combined Patch + Verify:
  - keep `request.repo_path` as the authoritative repo scope,
  - create a worktree from current `HEAD`,
  - pass only the resulting internal `execution_repo_path` to `patch_apply`,
  - and, for combined flow, pass the same `execution_repo_path` to `verification_run`.
- Standalone verification continues to use `request.repo_path`.
- Expose read-only worktree status queries through existing `/chat.answer`.

## Preconditions

- Target repo MUST be a non-bare Git repository with a valid `HEAD`.
- `.repopilot/` MUST be ignored by Git.
- Main workspace MUST have no tracked changes and no non-ignored untracked files.
- Ignored files MAY exist and MUST NOT block worktree creation.

## Internal Interfaces

- `WorktreeManager.create(...)` returns a `WorktreeCreateResult` with:
  - `worktree_id`
  - `execution_repo_path`
  - `base_commit`
  - `status`
  - `public_summary`
- `ToolExecutor.worktree_create(repo_path, user_id, patch_id)` delegates to
  `WorktreeManager`.
- `ToolInvocationContext` grows only the fields needed to validate `worktree_create`; it MUST NOT carry local paths.
- `patch_apply` and combined `verification_run` consume `execution_repo_path` only within the current request stack.

## Persistence And State

- Worktree store keeps:
  - `worktree_id`
  - `user_id`
  - `repo_key`
  - `patch_id`
  - `base_commit`
  - `status`
  - `verification_label`
  - `verification_status`
  - changed file summaries
  - timestamps
- Patch store adds `applied_in_worktree` as a new terminal state.
- Historical `applied` rows remain unchanged and valid.

## Failure Semantics

- Worktree create failure:
  - rollback incomplete registration / path creation best-effort,
  - patch remains `pending`,
  - no verification runs.
- Worktree metadata persistence failure:
  - treated as create failure with same rollback semantics.
- Patch apply failure inside worktree:
  - patch becomes `failed`,
  - worktree becomes `patch_failed`,
  - verification MUST NOT run,
  - V20 offers no retry.
- Verification failure:
  - patch remains `applied_in_worktree`,
  - worktree becomes `verification_failed`,
  - worktree remains available for inspection,
  - V20 offers no rerun.

## Queries And Public Output

- Supported read-only queries:
  - `查看 worktree <worktree_id>`
  - `worktree status <worktree_id>`
- Query result MAY include `worktree_id`, base commit, patch id, status, changed-file summary, verification label/status, and timestamps.
- Queries MUST NOT run Git mutation, patch apply, verification, task resume, or repo RAG.
- Public answers and persistent audit MUST redact local absolute paths, `.git` paths, DB paths, stdout/stderr, full diff, and secrets.

## Security Boundary

- Git subprocess calls are fixed argv with `shell=False`.
- User messages never control Git arguments, worktree paths, commit-ish, or branch names.
- Only `worktree_create`, `patch_apply`, and `verification_run` may mutate repo-local state in V20.

## Test Strategy

- Use temporary real Git repositories to verify worktree creation and lock behavior.
- Use targeted doubles for ToolExecutor call path assertions where needed.
- Keep TDD shape:
  - RED for new worktree behavior,
  - GREEN with minimal runtime changes,
  - REFACTOR after behavior is covered.
