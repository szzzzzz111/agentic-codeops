## Risk Level

Risk: `medium`.

Reason: this stage adds a user-facing command surface and package entrypoint, but it should remain a thin local wrapper over existing runtime behavior. It does not add new persistence, Git mutation semantics, provider wiring, network dependency, public API fields, verification labels, or V24 promotion.

## Current Behavior

RepoPilot currently exposes `POST /chat` through FastAPI and has an internal `ChatService` that calls `CodeAgent` and `AgentLoop`. README documents a planned CLI, and `openspec/specs/demo-ready-agent-cli/spec.md` records that the CLI must be a thin wrapper. There is no `repopilot` console command, no `app/cli.py`, and no CLI tests.

## Target Behavior

Add a local command:

```text
repopilot ask "<question>"
repopilot patch "<request>"
repopilot patch confirm <patch_id> [--verify verify|pytest|ruff]
repopilot verify <verify|pytest|ruff>
repopilot status
repopilot audit latest
```

Global options:

- `--repo <path>`: defaults to `.`.
- `--user-id <id>`: defaults to `cli`.
- `--session-id <id>`: defaults to `cli`.

The CLI constructs a `ChatRequest` and calls `ChatService.handle_chat()` directly. It prints a deterministic human-readable summary:

- `trace_id`
- `answer`
- optional `related_files`
- optional `tool_calls`

The first implementation does not need JSON output, streaming, colors, progress UI, config files, or environment-based provider controls.

## Command Mapping

- `ask "<question>"` sends the question unchanged.
- `patch "<request>"` sends the request unchanged and relies on existing PatchManager routing.
- `patch confirm <patch_id>` sends `confirm patch <patch_id>`.
- `patch confirm <patch_id> --verify <label>` sends `confirm patch <patch_id> and run <label>`.
- `verify <label>` sends `run <label>`.
- `status` sends `assistant status`.
- `audit latest` sends `audit latest`.

If implementation finds an existing parser requires a different exact phrase, the mapping may use the minimal existing phrase but must preserve the public CLI syntax above.

## Data Returned And Not Returned

Returned:

- request result status through process exit code;
- `trace_id`, `answer`, and bounded existing `related_files` / `tool_calls` summaries.

Not returned:

- full Evidence Pack;
- provider prompt/output;
- full diff;
- full stdout/stderr beyond existing verification answer boundaries;
- DB path, local absolute execution path, environment variables, or secrets.

## Exit Codes And Errors

- `0`: `ChatService` completed and returned a response, even if the underlying answer reports a rejected or failed RepoPilot operation.
- `2`: CLI usage or validation error, such as missing args, unsupported subcommand, invalid verification label, unsafe patch id, or unsafe syntax-like CLI value.
- `1`: unexpected CLI wrapper failure before a safe RepoPilot response can be produced.

The CLI should not swallow Python exceptions into raw tracebacks by default. It should print a short safe error line to stderr.

## Security And Boundaries

- Use `argparse` with structured arguments, not shell string parsing.
- Never pass user input to `subprocess`.
- Do not add arbitrary command execution.
- Do not accept verification labels beyond `verify`, `pytest`, and `ruff`.
- Validate `patch_id` with the existing safe patch id shape or a narrow local regex before mapping to a message.
- Resolve no extra filesystem paths beyond passing `--repo` to existing ChatService behavior.
- Do not read `.env`, provider keys, or config files.
- Do not change `/chat` schemas or AgentLoop routing.

## Trace And Audit

The CLI creates no independent audit store. It reuses whatever `ChatService` / `AgentLoop` already records for the mapped request. CLI output may print `trace_id`, but must not add new persistent audit payloads.

## Non-Goals

- No V24 promotion.
- No commit, merge, push, PR creation, branch management, or worktree promotion.
- No HTTP client mode.
- No new API endpoint or `/chat` field.
- No default CI change.
- No live provider profile, pricing, rubric, fixture, or evaluator change.
- No real model patch provider wiring.
- No background worker, scheduler, subagent, connector, notification, or always-on assistant behavior.

## Planned RED Cases

- CLI parser calls `ChatService` with the expected message for each command.
- `patch confirm --verify` accepts only `verify`, `pytest`, and `ruff`.
- Unsafe verification labels, pipes, redirects, env assignment, and extra args are rejected before `ChatService`.
- Unsafe patch ids are rejected before `ChatService`.
- CLI output includes `trace_id` and `answer` without exposing raw response internals.
- CLI errors return exit code 2 for usage/validation and do not print traceback.
- `pyproject.toml` exposes `repopilot = "app.cli:main"` without adding dependencies.

## Review Target

Internal review plus focused external review are expected before archive because this is a new user-facing command surface. Review should focus on command parsing, safety gates, message mapping, exit codes, no new network dependency, and no bypass around existing confirmation/verification boundaries.
