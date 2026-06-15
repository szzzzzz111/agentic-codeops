---
name: openspec-stage-planner
description: Use when starting a new RepoPilot stage, planning V5 or later work, creating an OpenSpec change, or deciding scope before modifying code in this repository.
---

# OpenSpec Stage Planner

## Core Rule

Plan the stage before implementation. OpenSpec defines the change; Harness defines the writable boundary.

## Workflow

1. Read `AGENTS.md`, `HANDOFF_TO_NEXT_CHAT.md`, `docs/PROGRESS.md`, and `openspec/README.md`.
2. Confirm the branch and dirty state. Do not overwrite unrelated user changes.
3. Create or update one OpenSpec change for the stage.
4. Write Chinese-first proposal/design/tasks/spec delta with required `SHALL` / `MUST` keywords in requirements.
5. Update `.harness/allowed_files.md` before code edits.
6. Update `.harness/review_checklist.md` before implementation review.
7. Keep runtime scope narrow; explicitly list non-goals.
8. Complete the planning `Manual Judgment Gates`: intent/scope, safety/architecture, planned test adequacy,
   review triage approach, semantic parity targets, and archive/merge/handoff risks.
9. Validate the OpenSpec change before implementation, then stop at the implementation confirmation gate.

## RepoPilot Scope Guards

- Do not write OpenSpec, Superpowers, MCP, plugin, or external skill support as runtime behavior unless the stage requires it.
- Do not claim LLM, RAG, Memory, Reflection, PermissionPolicy, ApprovalGate, SandboxRunner, eval, skill execution, or `/chat` skill decisions are implemented unless the code implements them.
- Prefer small stages: spec, tests, implementation, docs, verify.
- OpenSpec validation proves artifact structure, not plan quality; the planning Manual Judgment Gates remain required.

## References

Read `references/stage-template.md` when drafting a new stage or checking whether a proposed stage is too broad.
