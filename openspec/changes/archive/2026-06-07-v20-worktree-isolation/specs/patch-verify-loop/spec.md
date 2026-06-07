## ADDED Requirements

### Requirement: Combined Patch Verify Loop Reuses One Worktree

系统 SHALL create one isolated worktree for each valid combined Patch + Verify request. Both `patch_apply` and the follow-up white-listed verification run MUST execute against that same isolated execution repo path.

If worktree creation fails, the patch MUST remain `pending`, the combined request MUST stop before `patch_apply`, and verification MUST NOT run.

#### Scenario: Combined flow stops before apply when worktree creation fails

- **WHEN** a combined confirmation passes parsing but worktree creation fails
- **THEN** the system returns a safe failure summary
- **AND** the pending patch remains `pending`
- **AND** no verification runs
