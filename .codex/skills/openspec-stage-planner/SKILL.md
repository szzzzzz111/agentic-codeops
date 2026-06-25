---
name: openspec-stage-planner
description: Use when starting or reshaping a RepoPilot stage, creating an OpenSpec change, choosing risk level, or defining scope before repository implementation.
---

# OpenSpec Stage Planner

## Core Rule

Plan one small stage before implementation. OpenSpec owns the change contract;
Harness owns the writable and review boundary.

## Workflow

1. Read `AGENTS.md`, required project docs, and `openspec/README.md`.
2. Confirm branch, worktree, active changes, and unrelated local modifications.
3. Classify risk as `low`, `medium`, or `high`; state why.
4. Create or update one OpenSpec change with intent, non-goals, exact contracts,
   failure behavior, and acceptance evidence.
5. Update `.harness/allowed_files.md` and `.harness/review_checklist.md` before
   implementation.
6. Name only the durable docs whose owned facts will actually change.
7. Define the internal review target and whether Codex independent plan review
   and OpenCode independent plan review are required. Medium/high stages require
   both before implementation.
8. Complete internal plan review of proposal, design, tasks, spec deltas, test
   plan, and Harness boundaries against each other. Fix contradictions before
   validation.
9. For required external plan review, collect Codex independent plan review and
   OpenCode independent plan review findings or explicit no-findings conclusions,
   then triage every finding before implementation.
10. Validate the change, summarize stage-level decisions in plain language, and
   stop at the implementation confirmation gate.

## Scope Guards

- Do not describe OpenSpec, Superpowers, MCP, plugins, or local skills as
  RepoPilot runtime capabilities.
- Do not claim roadmap capabilities are implemented.
- Do not make every durable document mandatory by default.
- Planning validation proves artifact structure, not design quality.
- OpenCode plan review should reuse a relevant existing review session when
  possible; terminal timeout is not a verdict until the session is inspected for
  final assistant review text.
- Ask the human partner about intent, non-goals, and sequencing, not line-level
  code review.

## References

Read `references/stage-template.md` when drafting a stage or checking scope.
For end-to-end execution, return control to `repo-stage-workflow`.
