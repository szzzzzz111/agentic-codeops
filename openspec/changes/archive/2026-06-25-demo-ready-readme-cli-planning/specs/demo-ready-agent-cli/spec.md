## ADDED Requirements

### Requirement: Demo-ready CLI Is Planned As A Thin Wrapper

RepoPilot SHALL plan a future local `repopilot` CLI as a thin wrapper over existing RepoPilot capabilities, not as a replacement for `AgentLoop`, `ToolExecutor`, `VerificationRunner`, Audit, Worktree, or `/chat` contracts.

The CLI planning MUST distinguish implemented runtime capabilities from planned command packaging. Until a later implementation change lands, docs MUST NOT claim that a `repopilot` command is available.

#### Scenario: Planning does not create CLI runtime

- **WHEN** the `demo-ready-readme-cli-planning` change is active
- **THEN** it MAY define intended CLI commands and demo flow
- **AND** it MUST NOT add CLI runtime code, package entrypoints, command tests, or default CI changes

### Requirement: Planned CLI Preserves Existing Safety Boundaries

The planned CLI SHALL reuse existing explicit confirmation, fixed verification label, worktree, and redacted audit boundaries.

It MUST NOT accept arbitrary shell text, user-supplied argv fragments, pipes, redirects, environment assignment, extra verification arguments, implicit patch apply, promotion, commit, merge, push, background execution, network dependency, or V24 behavior.

#### Scenario: Patch proposal remains separate from apply

- **WHEN** a future user runs a patch proposal command
- **THEN** the command MUST create or report a pending patch proposal only
- **AND** it MUST NOT apply the patch unless a separate explicit confirmation command is used

### Requirement: Demo Flow Uses Existing Deterministic Capabilities By Default

The planned CLI SHALL support a demo path that can run without network by default: grounded question answering, pending patch proposal, explicit confirm apply, fixed-label verification, and redacted audit/status review.

Optional real model provider configuration MAY be documented for separate demos, but MUST NOT become required for deterministic verification or default CI.

#### Scenario: Default demo avoids network dependency

- **WHEN** the planned demo is executed with default local configuration
- **THEN** it MUST rely on deterministic local behavior and fixed verification labels
- **AND** it MUST NOT require provider API keys, live eval profile changes, model downloads, or external services
