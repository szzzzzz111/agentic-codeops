## Context

RepoPilot 当前已经有真实 runtime primitives：`ToolRegistry` 注册 `repo_rag`、`patch_apply`、`worktree_create`、`worktree_dispose` 和 `verification_run`，`PermissionPolicy` / `ApprovalGate` 决定这些工具何时可执行，其他 managers 提供 Memory、Long Task、Audit 和 worktree lifecycle 边界。

现有 capability-status 回答位于 `app/harness/kernel.py` 的静态字符串常量中，Assistant Control Surface 也在 `app/assistant/control_surface.py` 手写“当前能力”。这些回答曾多次需要跟随阶段演进修正。下一阶段不应该做一份独立手写注册表，而应把真实工具规格和固定安全边界翻译为用户可理解的能力语义。

风险级别：`medium`。理由是本阶段影响用户可见 capability/status 文案和 AgentLoop 内部能力状态装配，但不新增执行能力、不修改 `/chat` public contract、不引入持久化/权限/subprocess/Git mutation 新路径。

## Goals / Non-Goals

**Goals:**

- 从真实 `ToolRegistry` primitive 派生 capability availability。
- 让 capability-status 回答能区分“runtime primitive 已注册、可能在有效上下文和审批后可用”与“执行能力不可用”。
- 让 Assistant Control Surface 复用同一份结构化能力事实，避免 status 文案与 capability-status 文案各自漂移。
- 保留当前 route 优先级、`related_files=[]`、`tool_calls=[]` 和脱敏边界。
- 增加 regression tests，证明缺失 backing tool 时不会继续宣称相关执行能力可用。

**Non-Goals:**

- 不实现 MCP server、MCP tool discovery、动态工具注册或外部 descriptor endpoint。
- 不执行 Skill，不改变既有 Skill metadata/content loader 行为。
- 不实现 connector、runtime subagent、background worker、durable execution loop、always-on assistant 或 notification。
- 不新增 `/chat` 字段，不新增 CLI 子命令，不改变 provider runtime、live eval、默认 CI 或网络依赖。
- 不把 OpenSpec、Codex/OpenCode skills、Superpowers、MCP 或 plugin 写成 RepoPilot runtime 能力。

## Decisions

### Decision 1: Use an adapter, not a standalone hand-written catalog

Implement a small internal adapter that consumes runtime metadata, beginning with `ToolRegistry`, and returns normalized structured capability facts. This keeps the source of availability tied to registered primitives while still allowing product-level language such as approval requirements, fixed labels and non-goals.

Alternative considered: create a static JSON capability catalog. Rejected because it would duplicate `ToolRegistry` and could drift in exactly the way this stage is meant to prevent.

### Decision 2: Keep `ToolRegistry` as primitive metadata only

`ToolRegistry` should expose a safe read-only snapshot/list method, but it should not decide product capability wording and should not dispatch tools. The adapter maps primitive facts into capability claims.

Alternative considered: put all capability wording directly into `ToolRegistry`. Rejected because `ToolRegistry` is an execution metadata boundary; mixing product statements and non-goals into it would make permission and status responsibilities blurry.

### Decision 3: Preserve route and public response contracts

Capability-status remains inside `RequestRouter` and returns an ordinary `AgentLoopResult` with no tool calls. Assistant Control Surface remains a pre-router explicit status branch. Both use existing `/chat.answer`.

The adapter output is structured, not a paragraph that every consumer prints verbatim. Capability-status may keep stage-oriented wording such as V11/V12/V13/V16/V25 when answering specific capability questions. Assistant Control Surface must keep the existing concise style: a short affirmative current-capabilities sentence plus Memory/Long Task state and next commands. It must not dump full stage-versioned capability-status blocks into the generic status answer.

AgentLoop owns the active `ToolRegistry`, so it must also own wiring the active registry-derived capability facts into Assistant Control Surface. The control surface must not silently instantiate a default registry when the parent loop was configured with a custom registry. A standalone `AssistantControlSurface` may keep a default local capability provider for direct tests or ad hoc use, but AgentLoop status requests must pass the same active capability facts used by capability-status.

Alternative considered: add a public `/capabilities` endpoint or new `/chat.capabilities` field. Rejected as unnecessary API expansion for this stage.

### Decision 4: Make unavailable primitives fail closed in wording

When a custom `ToolRegistry` lacks a backing primitive, the derived answer must not claim that execution path is currently available. It may still state the intended non-goals and explain that the runtime primitive is not registered in the current loop.

This adapter is not a per-request eligibility engine. A registered write-risk primitive means the capability may be available through existing routes when a valid `ToolInvocationContext`, approval and safety preflight are produced; it does not mean arbitrary user text can directly invoke the tool.

Alternative considered: keep current historical-stage wording independent of custom registries. Rejected because tests already instantiate custom registries and this would hide wiring drift.

## Risks / Trade-offs

- Runtime-derived wording may be more verbose than the current static strings -> keep the adapter output bounded and focused on capability group summaries.
- `ToolRegistry` alone cannot express all product constraints -> pair registry presence with explicit known safety boundaries such as fixed verification labels and approval requirements.
- Assistant Control Surface could accidentally become a general capability discovery API -> keep it in the existing answer text, no new schema, and no descriptor export.
- Tests may overfit exact Chinese prose -> assert key facts and non-goals rather than entire paragraphs where possible.

## Migration Plan

1. Add RED tests for registry-derived capability status and Assistant Control Surface reuse.
2. Add the smallest adapter and read-only registry snapshot needed for those tests.
3. Wire capability-status and Assistant Control Surface through the adapter without changing route order. For Assistant Control Surface, pass the active loop's registry-derived facts rather than letting the control surface infer a separate default registry.
4. Run focused tests, `ruff check .`, `openspec validate --all`, full `scripts/verify.ps1`, and plan/final review gates.

Rollback is straightforward: the adapter is internal and can be removed while restoring previous static answer functions. No persistent data migration is involved.
