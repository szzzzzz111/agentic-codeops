## Current Behavior

当前 V6 Kernel 通过 `RequestRouter` 将请求路由到 `chat_only` 或 `repo_search`。`repo_search` 路径在调用 `ToolExecutor.search_code` 前只通过 `ToolRegistry` 校验工具是否存在、是否只读、风险等级是否为 `low`。拒绝事件记录在内部 trace 中，`/chat` 顶层响应不返回 trace events。

## Target Behavior

V7 在现有链路上增加确定性权限和审批边界：

```text
route -> registry lookup -> permission policy -> approval gate -> executor
```

- `ToolRegistry` 只负责登记和读取 `ToolSpec`，不再提供独立 allow/deny gate，也不负责权限原因判断。
- `PermissionPolicy` 是唯一状态校验边界，输出 `PermissionDecision(status)`，其中 `status` 只允许 `allow`、`deny`、`ask`。
- `ApprovalGate` 只消费 `PermissionPolicy` 的结果，不二次校验状态、不做真实交互审批、不持久化审批记录。
- `allow` 分支继续调用 `ToolExecutor.search_code` 并保持现有 `related_files` / `tool_calls` 行为。
- `deny` 分支返回固定回答、空 `related_files`、空 `tool_calls`，记录 `tool_rejected`。
- `ask` 分支返回固定回答、空 `related_files`、空 `tool_calls`，记录 `approval_required`。
- `chat_only` 路径不进入 permission/approval 链路，不记录 `permission_checked`。

## Minimal Contracts

- `ToolSpec(name, description, read_only, risk, requires_approval=False)`：
  - `requires_approval` 表示低风险只读工具是否仍需要人工审批。
  - 默认 `search_code` 为 `requires_approval=False`。
- `PermissionDecision(tool_name, status, reason)`：
  - `status` MUST 只由 `PermissionPolicy.decide` 产出。
  - `status` MUST 只允许 `allow`、`deny`、`ask`。
  - `reason` MUST 使用稳定机器可测字符串。
- `PermissionPolicy.decide(tool_spec)`：
  - 未注册工具、`read_only=False` 或 `risk!="low"` MUST 返回 `deny`。
  - 否则 `requires_approval=True` MUST 返回 `ask`。
  - 否则 MUST 返回 `allow`。
- `ApprovalGate.evaluate(decision)`：
  - `allow` 允许继续进入 executor。
  - `ask` MUST 阻止工具执行。
  - `deny` MUST 阻止工具执行。
- `AgentLoop`：
  - MUST 负责记录 `permission_checked`、`tool_rejected` 和 `approval_required` trace events。

## Trace and Response Semantics

V7 的审计事件仅记录在内部 `trace_events_internal`，有意不在 `/chat` 暴露。`/chat` 不返回拒绝或审批摘要，因此 `deny` 和 `ask` 分支的 `tool_calls` MUST 为 `[]`。

- `allow` trace 顺序 MUST 为 `request_routed -> permission_checked -> tool_call -> tool_result`。
- `deny` trace 顺序 MUST 为 `request_routed -> permission_checked -> tool_rejected`。
- `ask` trace 顺序 MUST 为 `request_routed -> permission_checked -> approval_required`。
- `chat_only` trace 顺序 MUST 仅为 `request_routed`。

固定回答：

- `deny`：`仓库工具未通过权限策略校验，因此本次没有执行仓库工具。`
- `ask`：`工具调用需要人工审批，因此本次没有执行仓库工具。`
- `chat_only`：沿用 `未提取到可搜索关键词，因此没有调用仓库工具。`

## Non-goals

- 不实现真实审批 UI 或审批持久化。
- 不新增写文件、删文件或 shell 工具。
- 不实现 SandboxRunner。
- 不接真实 LLM。
- 不执行 skill。
- 不做 RAG、Memory、Reflection、eval 或复杂多 Agent。
- 不新增 `/chat` 顶层响应字段。

## Security and Boundaries

- 所有实际仓库搜索仍 MUST 经由 `ToolExecutor.search_code`。
- Permission/Approval 只控制是否允许进入 executor，不绕过安全文件工具。
- Trace summary MUST 保持脱敏，不包含完整文件内容或本机绝对路径。
- 对外返回的 `related_files` MUST 只包含相对仓库路径；如果上游工具异常返回本机绝对路径，Kernel MUST 跳过该路径，避免通过 `/chat` 泄露。
