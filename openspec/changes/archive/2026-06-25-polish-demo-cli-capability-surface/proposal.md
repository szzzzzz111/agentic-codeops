## Why

RepoPilot now has a local `repopilot` CLI, but the surface still reads like a raw wrapper:
patch requests depend on the user's wording, output is a flat field dump, and the project
workflow does not yet make plan-level internal, Codex, and OpenCode review a hard
implementation gate. V24 should make the existing harness capabilities clearer for demo and
interview use without widening runtime power.

## What Changes

- Redefine V24 as CLI Capability Surface / Demo-ready Product Surface; move the previous
  Verified Patch Promotion roadmap item to V25/backlog and keep it out of this stage.
- Polish `repopilot` output into human-readable sections based only on existing public
  `trace_id`, `answer`, `related_files`, and `tool_calls`.
- Map `repopilot patch "<request>"` to the exact existing patch intent message
  `create patch: <request>` so patch proposal behavior does not depend on user wording.
- Tighten CLI patch id validation to the runtime-compatible and length-bounded
  `^patch_[A-Za-z0-9_]{1,122}$`.
- Harden RepoPilot planning workflow skills so implementation cannot start until internal
  plan review, Codex independent plan review, and OpenCode independent plan review have
  completed and findings have been triaged.
- Document OpenCode review handling: reuse existing review sessions first, and when terminal
  output times out inspect the session for final review text before marking the gate failed.
- Do not change `/chat` contract, AgentLoop, ToolExecutor, VerificationRunner, Audit,
  Worktree, provider runtime, live eval, default Patch wiring, default CI, network
  requirements, promotion, commit, merge, push, subagents, or connectors.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `demo-ready-agent-cli`: make the local CLI a clearer demo-ready product surface while
  remaining a thin `ChatService` wrapper.
- `harness-development-workflow`: require plan-level internal, Codex, and OpenCode review
  gates before implementation for medium/high RepoPilot stages.

## Impact

- Code: targeted CLI presentation and CLI argument validation only.
- Tests: focused CLI tests plus adjacent parser/AgentLoop/ChatService regressions where needed.
- Docs: README, ARCHITECTURE, FEATURE_LIST, PROGRESS, HANDOFF, OpenSpec specs, and Harness
  boundaries for changed owned facts.
- Process skills: `.codex/skills` planning/review workflow skills and a minimal OpenCode
  review workflow entry.
- Dependencies: no new runtime dependency and no network requirement.
