## Risk Level

Risk: `low` for this planning/README stage.

Reason: the stage changes documentation and OpenSpec/Harness boundaries only. It does not modify runtime code, tests, provider configuration, live eval profiles, default CI, default Patch wiring, `/chat` public contract, or worktree/promotion behavior.

If a later stage implements the CLI entrypoint, that implementation should be reclassified separately, likely `medium`, because it will add a user-facing command surface over existing patch, verification, worktree, and audit operations.

## Current Behavior

README currently starts with recent stage history and DeepSeek/V23 closeout notes before the project positioning. This makes the first viewport read like an internal development log instead of a concise project front door.

RepoPilot runtime currently already includes:

- `AgentLoop` orchestration behind `POST /chat`.
- repo-local deterministic query understanding and hybrid RAG.
- internal Evidence Pack, citation validation, and grounded answer boundary.
- Safe Patch Authoring with pending patch storage and explicit confirm apply.
- Verification Runner with fixed labels `pytest`, `ruff`, and `verify`.
- explicit Patch + Verify Loop.
- Worktree isolation/inventory/re-verification/disposal for retained patch worktrees.
- repo-local SQLite persistent audit/recovery/status.
- live model provider eval tooling and tracked attestation/failure artifacts.

RepoPilot does not currently ship a `repopilot` CLI command. Default patch authoring still uses the fake patch provider and does not generate real diffs unless a caller explicitly injects a real provider in custom wiring.

## Target README Facade

README top should become a compact GitHub/简历 first viewport:

- H1 stays `RepoPilot`.
- First paragraph states: 面向代码仓库理解、受控 Patch 和验证闭环的本地 Coding Agent Harness.
- Follow with a short value proposition for interviewers: not a general AI IDE replacement, but a controllable local harness for bounded tool calls, evidence-grounded answers, safe patch proposals, verification, worktree isolation, and audit handoff.
- Show current core capabilities in a compact list without implying roadmap features are implemented.
- Include a small text architecture or flow diagram.
- Keep quick start and detailed documentation links visible.
- Move stage history and deep closeout details below the project overview or behind document links.

The README MUST NOT say the CLI exists until implementation is completed in a later confirmed stage.

## Planned CLI Surface

The planned CLI is a thin local entrypoint over existing capabilities. Candidate commands:

- `repopilot ask "<question>"`: produce a grounded answer using existing AgentLoop/RAG/answering behavior.
- `repopilot patch "<request>"`: create a pending patch proposal through existing patch proposal flow; do not apply by default.
- `repopilot patch confirm <patch_id> [--verify <label>]`: explicit apply, optionally followed by fixed-label verification, using existing patch/verify/worktree semantics.
- `repopilot verify <label>`: run existing fixed verification labels, initially `pytest`, `ruff`, or `verify`.
- `repopilot status`: return the existing read-only assistant/recovery status summary.
- `repopilot audit latest`: show the latest redacted audit/status summary for the current scope.

The exact command syntax may be narrowed during CLI implementation, but the implementation MUST preserve these constraints:

- Reuse existing `AgentLoop`, `ToolExecutor`, `VerificationRunner`, Audit, and Worktree capabilities.
- Do not rewrite AgentLoop.
- Do not modify `/chat` request/response contract.
- Do not change default CI.
- Do not introduce network dependency.
- Do not accept arbitrary shell text, user-supplied argv fragments, environment assignments, pipes, redirects, or extra verification arguments.
- Do not make patch apply implicit; apply remains explicit confirmation.
- Do not promote, commit, merge, push, or implement V24.
- Do not describe default fake patch proposals as real diffs.

## Demo Path

The intended demo recording path is:

1. Ask a code-location or implementation question.
2. Show a grounded answer with citation-backed related files.
3. Request a patch proposal and show pending patch metadata.
4. Explicitly confirm apply.
5. Run deterministic verification by fixed label, preferably `verify`.
6. Show audit/status for the latest operation.

This path must work without network by default. If a real model provider is configured for a separate live demo, that must be described as optional configuration, not default behavior.

## Current vs Planned Claims

Allowed current claims:

- RepoPilot currently has AgentLoop, repo-local hybrid RAG, Evidence Pack/citation, grounded answer boundary, Safe Patch Authoring, Verification Runner, Patch + Verify, Worktree isolation/lifecycle, SQLite audit/recovery, and live model eval tooling.

Allowed planning claims:

- A demo-ready CLI is planned as a thin wrapper over existing capabilities.
- Candidate command names are provisional until implementation and tests land.

Forbidden claims:

- Do not claim `repopilot` CLI is implemented.
- Do not claim default runtime generates real model-authored diffs.
- Do not claim V24 verified promotion, commit, merge, push, arbitrary shell, background workers, connectors, subagents, or always-on assistant are implemented.
- Do not describe OpenSpec, Superpowers, MCP, plugins, or local skills as RepoPilot runtime features.

## Review Target

Internal review for this planning stage should check:

- README first-viewport truthfulness and interview readability.
- CLI planning stays thin and does not smuggle runtime/API/CI changes.
- Harness allowed files exclude runtime and tests.
- Durable docs only change facts they own.

No independent external review is required before planning approval because this stage is docs/planning only. External review should be reconsidered if the later CLI implementation touches command parsing, patch apply, verification execution, audit, or worktree behavior.

## Acceptance Evidence

- `openspec validate demo-ready-readme-cli-planning --strict`
- `openspec validate --all`
- `git diff --check`
- For README-only implementation after confirmation: focused manual review against README truthfulness checklist.
- No runtime/test files changed in this planning stage.
