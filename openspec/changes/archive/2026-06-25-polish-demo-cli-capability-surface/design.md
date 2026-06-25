## Risk Level

Risk: `medium`.

Reason: this stage changes a user-facing CLI surface and development workflow gates, but keeps
runtime behavior within existing `ChatService` and AgentLoop semantics. It does not add new
public API fields, provider wiring, persistence models, verification labels, worktree promotion,
or default CI behavior.

## Current Behavior

`repopilot` is implemented as a thin local CLI that constructs `ChatRequest` objects and calls
`ChatService.handle_chat()`. It prints `trace_id`, `answer`, optional `related_files`, and
optional `tool_calls`.

The current patch command sends `repopilot patch "<request>"` through unchanged. Runtime patch
proposal routing only recognizes explicit patch intent terms such as `create patch`, so a demo
request like `repopilot patch "change README wording"` is not stable unless the user's text
already contains a patch keyword.

The current CLI patch id regex is wider than the runtime confirmation parser. The CLI may accept
ids the runtime cannot confirm.

The current stage workflow records internal planning review and final implementation review, but
does not make plan-level Codex and OpenCode external review a hard pre-implementation gate.

README and architecture roadmap currently use `V24 Verified Patch Promotion` for a future
worktree-to-main-workspace promotion stage. This stage intentionally reassigns V24 to CLI
Capability Surface, so the promotion item must be moved to V25/backlog.

## Target Behavior

`repopilot` remains a local thin wrapper with the same supported commands:

```text
repopilot ask "<question>"
repopilot patch "<request>"
repopilot patch confirm <patch_id>
repopilot patch confirm <patch_id> --verify <verify|pytest|ruff>
repopilot verify <verify|pytest|ruff>
repopilot status
repopilot audit latest
```

Command mapping is fixed:

- `ask "<question>"` sends the question unchanged.
- `patch "<request>"` sends exactly `create patch: <request>`.
- `patch confirm <patch_id>` sends `confirm patch <patch_id>`.
- `patch confirm <patch_id> --verify <label>` sends
  `confirm patch <patch_id> and run <label>`.
- `verify <label>` sends `run <label>`.
- `status` sends `assistant status`.
- `audit latest` sends `audit latest`.

Patch id validation is fixed at `^patch_[A-Za-z0-9_]{1,122}$`, preserving runtime-compatible
syntax and the existing 128-character total limit.

CLI output becomes human-readable sections, still derived only from existing public response
fields. It must not read or imply access to internal Evidence Pack content, full diff,
provider prompt/output, full stdout/stderr, DB path, local absolute execution path, environment
variables, or secrets.

Planning workflow skills must say that medium/high stages cannot enter implementation until:

1. internal plan review has checked proposal/design/tasks/spec deltas/test plan/Harness;
2. Codex independent plan review has returned findings or a no-findings conclusion;
3. OpenCode independent plan review has returned final assistant review text;
4. all plan review findings have been classified as `fix`, `clarify`, `reject`, or `defer`.

OpenCode review should first reuse an existing relevant review session via `opencode session list`
and `opencode run --session <session_id> ...`. If terminal output times out, the reviewer must
inspect whether the session produced final assistant review text before treating the gate as
failed. Missing final text is a blocker unless the user explicitly authorizes a downgrade.

## Non-Goals

- No Verified Patch Promotion in this stage.
- No commit, merge, push, PR creation, branch management, or worktree promotion.
- No HTTP client mode, JSON output mode, streaming, colors, config files, or new CLI public schema.
- No new API endpoint or `/chat` field.
- No default CI change.
- No live provider profile, pricing, rubric, fixture, or evaluator change.
- No real model patch provider wiring.
- No background worker, scheduler, subagent runtime, connector, notification, or always-on assistant behavior.
- No changes to AgentLoop, ToolExecutor, VerificationRunner, Audit, Worktree, provider runtime, or default Patch wiring.

## Security And Boundaries

- Use structured `argparse` arguments, not shell string parsing.
- Never pass user input to subprocess from the CLI.
- Reject verification labels outside `verify`, `pytest`, and `ruff`.
- Reject unsafe patch ids before `ChatService` is called.
- Keep OpenSpec, local skills, OpenCode, MCP, plugins, and Superpowers documented as development
  workflow, not RepoPilot runtime capabilities.
- Do not add runtime reads of `.env`, provider keys, or config files.

## Planned RED Cases

- `repopilot patch "change app.py"` sends exactly `create patch: change app.py`.
- `create patch:` is accepted by existing patch proposal intent detection.
- CLI patch id validation accepts suffix lengths 1 and 122, rejects empty suffix, 123 suffix,
  hyphenated ids, missing `patch_` prefix, and unsafe shell-like characters.
- Output prints clear sections for `trace_id`, `answer`, `related_files`, and `tool_calls`.
- Existing `patch confirm`, `patch confirm --verify`, `verify`, `status`, and `audit latest`
  mappings remain stable.
- Workflow skill checks find plan-level internal, Codex, and OpenCode review gates and the
  OpenCode session reuse/timeout rule.
- README/ARCHITECTURE wording does not present Verified Patch Promotion, real model patch
  authoring, commit/push, subagents, or connectors as implemented.

## Review Target

Before implementation, complete internal plan review, Codex independent plan review, OpenCode
independent plan review, and finding triage. Final implementation review remains internal plus
focused external review because this is a medium-risk user-facing surface and workflow change.

Stage Debt Sweep should inspect changed CLI tests/runtime, directly dependent parser and
ChatService paths, workflow skills, OpenCode review entry, README/spec/Harness docs, and same-class
roadmap wording.
