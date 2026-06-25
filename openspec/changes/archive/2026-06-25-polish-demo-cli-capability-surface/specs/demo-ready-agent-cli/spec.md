## MODIFIED Requirements

### Requirement: Demo-ready CLI Is Planned As A Thin Wrapper

RepoPilot SHALL provide a local `repopilot` CLI as a thin wrapper over existing RepoPilot capabilities, not as a replacement for `AgentLoop`, `ToolExecutor`, `VerificationRunner`, Audit, Worktree, or `/chat` contracts.

The CLI MUST distinguish command presentation from runtime capability changes. It MUST call existing service/agent boundaries and MUST NOT claim or implement behavior outside those boundaries.

#### Scenario: CLI runtime delegates to existing ChatService

- **WHEN** a user invokes a supported `repopilot` command
- **THEN** the CLI constructs an equivalent existing chat request
- **AND** it calls `ChatService.handle_chat()`
- **AND** it prints a safe human-readable summary of the returned `trace_id`, `answer`, `related_files`, and `tool_calls`
- **AND** it MUST NOT add or require new `/chat` request or response fields

#### Scenario: Patch command injects stable proposal intent

- **WHEN** a user runs `repopilot patch "<request>"`
- **THEN** the CLI sends exactly `create patch: <request>` to `ChatService`
- **AND** the command MUST request a patch proposal only
- **AND** it MUST NOT apply the patch unless a separate explicit confirmation command is used

### Requirement: Planned CLI Preserves Existing Safety Boundaries

The CLI SHALL reuse existing explicit confirmation, fixed verification label, worktree, and redacted audit boundaries.

It MUST NOT accept arbitrary shell text, user-supplied argv fragments, pipes, redirects, environment assignment, extra verification arguments, implicit patch apply, promotion, commit, merge, push, background execution, network dependency, or Verified Patch Promotion behavior.

#### Scenario: Confirmed patch apply remains explicit

- **WHEN** a user runs `repopilot patch confirm <patch_id>`
- **THEN** the CLI maps it to an existing explicit patch confirmation message
- **AND** `<patch_id>` MUST match `^patch_[A-Za-z0-9_]{1,122}$`
- **AND** any apply behavior remains governed by existing PatchManager, ToolExecutor, PermissionPolicy, ApprovalGate, and worktree boundaries

#### Scenario: Verification labels remain whitelisted

- **WHEN** a user runs `repopilot verify <label>` or `repopilot patch confirm <patch_id> --verify <label>`
- **THEN** `<label>` MUST be one of `verify`, `pytest`, or `ruff`
- **AND** shell-like syntax, extra arguments, pipes, redirects, and environment assignment MUST be rejected before `ChatService` is called

### Requirement: Demo Flow Uses Existing Deterministic Capabilities By Default

The CLI SHALL support a demo path that can run without network by default: grounded question answering, pending patch proposal, explicit confirm apply, fixed-label verification, and redacted audit/status review.

Optional real model provider configuration MAY be documented for separate demos, but MUST NOT become required for deterministic verification or default CI.

#### Scenario: Default demo avoids network dependency

- **WHEN** the planned demo is executed with default local configuration
- **THEN** it MUST rely on deterministic local behavior and fixed verification labels
- **AND** it MUST NOT require provider API keys, live eval profile changes, model downloads, or external services

#### Scenario: CLI evidence summary uses only public response fields

- **WHEN** the CLI prints related files, tool calls, or demo evidence summaries
- **THEN** those summaries MUST be derived only from public `related_files` and `tool_calls`
- **AND** the CLI MUST NOT read, reconstruct, or claim access to internal Evidence Pack content or a new citation schema

#### Scenario: CLI exposes status and audit through existing read-only paths

- **WHEN** a user runs `repopilot status` or `repopilot audit latest`
- **THEN** the CLI MUST map the command to existing read-only assistant status or audit recovery semantics
- **AND** it MUST NOT mutate repository files except for existing audit behavior already owned by the mapped AgentLoop request
