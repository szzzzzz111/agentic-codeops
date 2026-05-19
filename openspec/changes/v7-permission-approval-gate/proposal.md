## Why

RepoPilot V6 已建立轻量 `AgentLoop`、`ToolRegistry`、`ToolExecutor` 和内存级 `TraceEvent`，但工具调用前的权限决策仍只停留在 registry 元数据校验。V7 需要在不引入高风险工具的前提下，把权限策略、审批占位和内部审计事件边界接入统一执行链路，为后续写文件、shell、SandboxRunner 等高风险能力留下明确入口。

## What Changes

- 在 Kernel 中新增确定性 `PermissionPolicy` 和最小 `ApprovalGate`。
- 扩展 `ToolSpec`，新增 `requires_approval` 字段，默认 `search_code` 仍为低风险只读且不需要审批。
- 固化权限优先级：未注册工具、非只读工具或非低风险工具进入 `deny`；低风险只读但 `requires_approval=True` 进入 `ask`；其余进入 `allow`。
- `AgentLoop` 在调用 `ToolExecutor` 前执行 registry lookup、permission policy 和 approval gate。
- `deny` 和 `ask` 分支不调用工具，`related_files` 和 `tool_calls` 均为空；拒绝/审批审计仅保留在内部 `trace_events_internal`，不通过 `/chat` 暴露。
- 保持 `/chat` 顶层响应结构不变，不新增 trace 字段。
- 新增和更新测试覆盖 allow、deny、ask、chat_only 的 trace 顺序和响应语义。

## Capabilities

### New Capabilities

- 无。

### Modified Capabilities

- `agent-loop-tool-execution`：工具调用链路从 registry gate 扩展为 registry lookup -> permission policy -> approval gate -> executor。

## Impact

- Code: `app/harness/kernel.py`
- Tests: `tests/test_agent_harness_kernel.py`, `tests/test_chat_api.py`
- Docs: `README.md`, `docs/ARCHITECTURE.md`, `docs/PROGRESS.md`, `docs/FEATURE_LIST.json`, `HANDOFF_TO_NEXT_CHAT.md`
- Harness: `.harness/allowed_files.md`, `.harness/review_checklist.md`
