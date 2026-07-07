## Why

RepoPilot 的 capability-status 和 Assistant Control Surface 当前仍依赖手写能力文案，容易与 `ToolRegistry`、权限边界和已归档能力事实漂移。下一阶段需要把“能做什么”的回答收敛为从真实 runtime primitives 派生的能力状态，同时继续明确 MCP、Skill、connector、subagent 等只是未开放的非目标或开发流程概念。

## What Changes

- 新增一个小型 capability status adapter：从现有 `ToolRegistry` 的真实工具规格和已实现的固定 runtime 边界派生用户可见能力状态。
- 修改 capability-status 回答，使 patch、verification、worktree、repo RAG 等能力声明必须由 backing runtime primitive 支撑；缺少 backing tool 时不得继续宣称对应执行能力可用。
- 修改 Assistant Control Surface 的“当前能力”段落，使 `助手状态` / `what can you do` 复用同一份 runtime-derived capability summary，而不是另写一份静态能力描述。
- 保持 `/chat` public contract 不变：仍只返回 `trace_id`、`answer`、`related_files`、`tool_calls`。
- 明确不实现 MCP server、Skill execution、connector、runtime subagent、background worker、动态工具注册、网络依赖或新的公开 descriptor API。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `agent-loop-tool-execution`: capability-status 回答必须从真实 runtime primitive 与安全边界派生，并在缺失 backing tool 时安全降级。
- `assistant-control-surface`: 控制面的当前能力摘要必须复用 runtime-derived capability summary，且仍保持只读、脱敏、不调用 repo RAG。

## Impact

- Code: `app/harness/kernel.py`, `app/assistant/control_surface.py`; 如实现需要，可新增 `app/harness/capabilities.py` 作为纯内部 adapter。
- Tests: `tests/test_agent_harness_kernel.py`, `tests/test_assistant_control_surface.py`, `tests/test_chat_api.py`。
- Docs: `.harness/allowed_files.md`, `.harness/review_checklist.md`, `docs/PROGRESS.md`, `HANDOFF_TO_NEXT_CHAT.md`；archive 后同步 `openspec/specs/agent-loop-tool-execution/spec.md` 和 `openspec/specs/assistant-control-surface/spec.md`。
- APIs/dependencies: 不新增公开 API，不新增 `/chat` 顶层字段，不新增依赖，不改变默认 CI、provider runtime 或 live eval。
