## Why

RepoPilot 已经具备 `/chat`、只读仓库工具、`ToolExecutor` 和 skill loader，但当前主链路仍像功能点串联，不像可演进的 Agent Harness。V6 需要先建立轻量 Agent Harness Kernel 和 Router Kernel，让后续 RAG、Memory、权限、长任务和 skill 演进都有稳定落点。

## What Changes

- 新增轻量 `app/harness/` Kernel 骨架，当前只包含 `RequestRouter`、`ToolRegistry`、`AgentLoop` 和 `TraceEvent` 的最小实现。
- 固化最小数据结构 contract：`RouteDecision`、`ToolSpec`、`TraceEvent` 和内部 `AgentLoopResult`。
- `ProviderAdapter`、`ContextBuilder`、`SkillRegistry` 和 `SessionStore` 仅作为后续扩展方向保留在设计说明中，V6 不写对应运行时代码。
- 让 `CodeAgent` 通过 Kernel 执行当前确定性仓库搜索闭环，保持 `/chat` 顶层响应结构不变。
- 将现有 `ToolExecutor.search_code` 注册为 Kernel 的只读低风险工具能力；运行时仓库搜索必须先经过 `ToolRegistry` 校验，再经过 `ToolExecutor`。
- 新增 Kernel 单元测试，覆盖路由、工具注册、trace event 和现有搜索闭环。
- 文档同步 V6 路线：工程化但轻量，优先体现边界、审计、验证、可替换接口和交接。

## Capabilities

### New Capabilities

- 无。

### Modified Capabilities

- `agent-loop-tool-execution`：Agent Loop 从 `CodeAgent` 内部规则扩展为通过轻量 Harness Kernel 编排 Router、ToolRegistry、ToolExecutor 和 TraceEvent。
- `harness-development-workflow`：V6 后续阶段路线改为轻量工程化，要求新阶段优先交付可运行纵向切片，避免重型依赖和过度抽象。

## Impact

- Code: `app/harness/__init__.py`, `app/harness/kernel.py`, `app/agents/code_agent.py`
- Tests: `tests/test_agent_harness_kernel.py`
- Docs: `README.md`, `docs/PROGRESS.md`, `docs/FEATURE_LIST.json`, `HANDOFF_TO_NEXT_CHAT.md`
- Harness: `.harness/allowed_files.md`, `.harness/review_checklist.md`
