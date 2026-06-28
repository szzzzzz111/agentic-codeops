## ADDED Requirements

### Requirement: Streaming Git Diff Inspection Is Timeout-Bounded

Worktree inspection SHALL use timeout-bounded process handling for streaming Git diff commands used by hunk count
and bounded preview. The timeout MUST cover both stdout consumption and process finalization. Streaming commands
MUST keep fixed argv, `shell=False`, and `GIT_OPTIONAL_LOCKS=0`.

When a streaming Git process times out, blocks while reading, fails to start, exits non-zero, or raises a subprocess
error, inspection MUST kill and reap the process when possible and safely degrade to a partial result without retry,
repair, mutation, raw stderr, raw exception text, local absolute paths, or unbounded stdout/diff exposure.

#### Scenario: Hunk count streaming timeout is partial

- **WHEN** the hunk-count Git diff process blocks or does not exit within the inspection streaming timeout
- **THEN** inspection kills and reaps the process
- **AND** hunk count returns only safe bounded information collected so far
- **AND** the inspection result is marked partial

#### Scenario: Preview streaming timeout omits affected file

- **WHEN** a per-file preview Git diff process blocks or does not exit within the inspection streaming timeout
- **THEN** inspection kills and reaps the process
- **AND** the affected file preview is omitted from the public answer
- **AND** the inspection result is marked partial
