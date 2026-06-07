## ADDED Requirements

### Requirement: Worktree-Backed Patch Apply Uses A Distinct Patch State

系统 SHALL mark a patch applied inside an isolated worktree as `applied_in_worktree`. This state indicates the patch was successfully applied in a retained worktree and MUST NOT imply the main working tree was modified.

Historical `applied` records MAY remain for older stages and MUST NOT be rewritten during V20 migration.

#### Scenario: Worktree-backed patch success uses isolated state

- **WHEN** a confirmed patch apply succeeds inside a V20 worktree
- **THEN** the patch store records `applied_in_worktree`
- **AND** the public answer MUST NOT state that the main working tree was changed
