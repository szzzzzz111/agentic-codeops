## 1. Harness

- [x] 1.1 Update `.harness/allowed_files.md` for this stage's planning and implementation scope.
- [x] 1.2 Update `.harness/review_checklist.md` with Grilling Gate summary, medium-risk plan review gates, implementation tasks and verification evidence placeholders.

## 2. Tests

- [x] 2.1 Add RED tests proving capability-status uses active `ToolRegistry` backing primitives and does not advertise missing execution tools as available.
- [x] 2.2 Add RED tests proving default capability-status still reports implemented patch, verification, worktree, promotion, grounded answer, rewrite/rerank and memory boundaries without repo RAG.
- [x] 2.3 Add RED tests proving Assistant Control Surface reuses runtime-derived structured capability facts while keeping concise generic status wording; it must not include stage-version markers or newly introduce MCP, Skill execution, connector or runtime subagent denial clauses.
- [x] 2.4 Add RED tests proving `AgentLoop(tool_registry=ToolRegistry(...))` passes the active registry-derived facts into Assistant Control Surface for `assistant status`, so missing execution primitives are not advertised there either.
- [x] 2.5 Keep adjacent `/chat` contract coverage for `trace_id`, `answer`, `related_files` and `tool_calls`.

## 3. Implementation

- [x] 3.1 Add a read-only `ToolRegistry` snapshot/list method that exposes registered `ToolSpec` metadata without dispatching tools.
- [x] 3.2 Implement the smallest internal capability status adapter needed to map registered runtime primitives plus fixed safety boundaries into capability summaries.
- [x] 3.3 Wire capability-status answers through the adapter while preserving `RequestRouter` route output, no repo RAG, and empty public `tool_calls`.
- [x] 3.4 Wire Assistant Control Surface current-capability text through the same adapter while preserving read-only Memory/Long Task status behavior; AgentLoop must pass active registry-derived facts rather than letting the control surface infer a separate default registry.

## 4. Review And Verification

- [x] 4.1 Run focused tests for AgentLoop capability status, Assistant Control Surface and Chat API contract.
- [x] 4.2 Run `ruff check .`.
- [x] 4.3 Run `openspec validate derive-capability-status-from-runtime --strict` and `openspec validate --all`.
- [x] 4.4 Complete internal plan review, Codex independent plan review and OpenCode independent plan review before implementation.
- [x] 4.5 After implementation, complete final implementation review and focused Stage Debt Sweep over changed runtime/tests/docs and directly dependent status/routing paths.
- [x] 4.6 Run full `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1` and `git diff --check`.
