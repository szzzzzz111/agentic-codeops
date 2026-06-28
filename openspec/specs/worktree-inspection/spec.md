# worktree-inspection Specification

## Purpose

定义 RepoPilot 按 `user_id + repo_key` 隔离的只读 worktree inventory / inspection，以及 bounded redacted preview、no-create 和 audit-skip 安全边界。
## Requirements
### Requirement: Worktree Inventory Is Scoped And Read-Only

系统 SHALL list at most the latest 20 worktree metadata records for the current `user_id + repo_key` scope, ordered deterministically by creation time and worktree id.

Missing stores and empty scopes MUST return an empty result without creating `.repopilot/`, a database, or any repository state.

#### Scenario: Missing store inventory creates no state

- **WHEN** the user requests `worktree list` and no worktree store exists
- **THEN** the system returns an empty inventory answer
- **AND** it MUST NOT create `.repopilot/` or a database

### Requirement: Worktree Inspection Reports Safe Consistency Evidence

系统 SHALL inspect a scoped worktree and report lifecycle metadata, patch id, base commit, tracked changed files, diffstat, hunk count, verification summary, and Git registry/directory/metadata consistency findings.

Inspection MUST NOT repair, reconcile, unlock, remove, discard, verify, promote, or otherwise mutate state. Unknown or cross-scope ids MUST stop before Git inspection.

#### Scenario: Inconsistent retained worktree is reported without repair

- **WHEN** metadata exists but the expected directory or Git registry entry is missing
- **THEN** inspection returns explicit safe inconsistency findings
- **AND** no repair or cleanup action runs

### Requirement: Preview Paths Come Only From Machine-Readable Git Output

系统 SHALL derive tracked preview paths only from fixed-argv `git diff --name-only -z --no-ext-diff --no-textconv <base_commit> --` output. Diffstat SHALL use fixed-argv `git diff --numstat -z --no-ext-diff --no-textconv <base_commit> --`.

User messages and persisted changed-file summaries MUST NOT drive per-file Git diff commands.

#### Scenario: User-supplied path cannot drive preview

- **WHEN** an inspection message includes an arbitrary repository path
- **THEN** the path is not used for a per-file diff
- **AND** only Git-derived safe tracked paths may be previewed

### Requirement: Diff Preview Is Bounded And Redacted

系统 SHALL format preview through a dedicated safe formatter with limits of 20 files, 6000 total characters, 80 lines per file, and 300 characters per line.

The formatter MUST reject binary files, sensitive files, hidden path components, `.git/**`, and `.repopilot/**`; MUST redact local absolute paths, DB paths, and common secrets; and MUST report omitted/truncated file, line, and character counts.

Raw Git diff output MUST exist only within the current inspection call stack and MUST NOT enter persistent audit, trace summaries, tool calls, or persistent/public data fields named `diff`, `diff_text`, or `full_diff`.

Patch-body and aggregate hunk-count commands MUST be consumed as streams without unbounded output capture. Only bounded redacted preview text and counters MAY be retained. Machine-readable metadata commands MUST enforce explicit output caps and return safe partial/unavailable findings when exceeded.

#### Scenario: Unsafe tracked file is omitted

- **WHEN** Git reports a binary, sensitive, hidden, or state-directory tracked path
- **THEN** the formatter omits its preview and increments omitted counters
- **AND** no content from that path is exposed

### Requirement: Untracked Files Are Count-Only

系统 SHALL report only the count of untracked files found during inspection. Public answers, traces, and persistent data MUST NOT include untracked file names, path prefixes, or content.

#### Scenario: Sensitive untracked filename is not exposed

- **WHEN** an inspected worktree contains an untracked sensitive filename
- **THEN** the answer may report that one untracked file exists
- **AND** it MUST NOT expose the filename or path

### Requirement: Public Inspection Metadata Is Bounded And Safe

系统 SHALL redact and bound metadata scalars and tracked changed-file summaries before placing them in `/chat.answer` or request-local trace summaries. Public changed-file summaries SHALL display at most 20 tracked paths and report an omitted count.

Read-only Git inspection MUST disable optional Git locks, and read-only SQLite access MUST use a no-write mode. Corrupt or unavailable worktree stores MUST return safe empty/not-found results instead of breaking `/chat`.

#### Scenario: Tampered metadata cannot leak through inventory

- **WHEN** repo-local worktree metadata contains secrets, state paths, control whitespace, or oversized values
- **THEN** inventory and inspection return bounded redacted summaries
- **AND** no raw metadata value enters the public answer or request-local trace summary

### Requirement: Worktree Git Metadata Reads Use A Hardened Shared Runner

系统 SHALL use a shared fixed-argv Git metadata runner for V21 inspection metadata reads. The runner MUST use `shell=False`, `GIT_OPTIONAL_LOCKS=0`, an independent timeout, and an output byte hard limit enforced before reading content.

Timeout, oversize, non-zero exit, malformed output, or exception MUST safely degrade inspection without retry or mutation.

#### Scenario: Oversize metadata safely degrades inspection

- **WHEN** Git metadata output exceeds the hard limit
- **THEN** inspection reports a safe partial result
- **AND** it MUST NOT read or expose the oversized content

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
