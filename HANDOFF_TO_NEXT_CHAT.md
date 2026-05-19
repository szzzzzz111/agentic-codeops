# 交接给下一轮 Chat

## 分支状态

```text
当前工作分支：feature/v7-permission-approval-gate
当前基线分支：main
当前活跃 OpenSpec change：v7-permission-approval-gate
```

## 当前项目状态

RepoPilot 当前定位为面向代码仓库分析任务的可控 Code Agent Harness，不是替代通用 AI IDE 的编程助手。V1-V6 已完成并进入长期规格/归档历史；当前 V7 主线是 Permission + Approval Gate。

当前主链路：

```text
API -> ChatService(trace_id) -> CodeAgent -> AgentLoop -> ToolRegistry -> PermissionPolicy -> ApprovalGate -> ToolExecutor -> file_tools
```

`/chat` 顶层响应仍保持现有 contract：`trace_id`、`answer`、`related_files`、`tool_calls`。V7 的权限和审批审计只保留在内部 `trace_events_internal`，不作为 `/chat` 顶层字段暴露。

## 本轮完成

- 创建 V7 分支：`feature/v7-permission-approval-gate`。
- 创建当前 OpenSpec change：`openspec/changes/v7-permission-approval-gate/`。
- 同步当前 V7 阶段 harness：
  - `.harness/allowed_files.md`
  - `.harness/review_checklist.md`
- 新增 V7 运行时边界：
  - `ToolSpec.requires_approval`
  - `PermissionDecision`
  - `PermissionPolicy`
  - `ApprovalGate`
- 收敛职责边界：`ToolRegistry` 只登记和读取 `ToolSpec`，不再保留独立 allow/deny gate；权限状态和拒绝原因由 `PermissionPolicy` 统一产出。
- 将 `AgentLoop` 工具调用前链路调整为：
  - route
  - registry lookup
  - permission policy
  - approval gate
  - executor
- 固化分支行为：
  - `allow`：继续调用 `ToolExecutor.search_code`。
  - `deny`：不调用 executor，返回固定权限拒绝回答，`related_files=[]`，`tool_calls=[]`。
  - `ask`：不调用 executor，返回固定审批回答，`related_files=[]`，`tool_calls=[]`。
  - `chat_only`：不进入 permission/approval 链路，不记录 `permission_checked`。
- 更新文档和功能清单：
  - `README.md`
  - `docs/ARCHITECTURE.md`
  - `docs/PROGRESS.md`
  - `docs/FEATURE_LIST.json`
  - `HANDOFF_TO_NEXT_CHAT.md`

## V7 边界

已实现：

- 确定性 `allow`、`deny`、`ask` 权限状态。
- 权限优先级：未注册、非只读或非 `low` 风险 -> `deny`；否则 `requires_approval=True` -> `ask`；否则 -> `allow`。
- 最小 `ApprovalGate`：只消费权限决策，遇到 `ask` 阻止工具执行。
- `AgentLoop` 负责记录 `permission_checked`、`tool_rejected` 和 `approval_required` trace event。
- `related_files` 只返回相对仓库路径，不返回本机绝对路径。
- 内部 trace 顺序：
  - `allow`：`request_routed -> permission_checked -> tool_call -> tool_result`
  - `deny`：`request_routed -> permission_checked -> tool_rejected`
  - `ask`：`request_routed -> permission_checked -> approval_required`
  - `chat_only`：仅 `request_routed`

V7 不做：

- 不实现真实审批 UI。
- 不持久化审批记录。
- 不新增写文件、删文件或 shell 工具。
- 不实现 SandboxRunner。
- 不接真实 LLM。
- 不执行 skill。
- 不做 RAG、Memory、Reflection、eval、复杂多 Agent 或长任务 Agent。
- 不新增 `/chat` 顶层响应字段。

## 本轮验证

- `openspec validate v7-permission-approval-gate`：通过。
- `pytest tests/test_agent_harness_kernel.py`：16 passed。
- `pytest tests/test_chat_api.py`：6 passed。
- `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`：通过。
  - `pytest`：46 passed, 1 skipped。
  - `ruff check .`：All checks passed。
- `git diff --check`：通过，仅有 CRLF 换行提示。

## 下一轮建议

1. 进行 review 并按反馈修正。
2. 提交 V7 分支。
3. 用户验收后归档 `v7-permission-approval-gate`。
