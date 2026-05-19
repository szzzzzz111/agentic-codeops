# agent-loop-tool-execution Delta

## MODIFIED Requirements

### Requirement: 工具调用经过 ToolRegistry、PermissionPolicy、ApprovalGate 和 ToolExecutor

系统 SHALL 使用 `ToolRegistry` 记录工具规格元数据，并且当前仓库搜索 MUST 继续通过 `ToolExecutor.search_code` 执行。`ToolRegistry` MUST NOT 负责实际 dispatch。

`AgentLoop` 调用工具前 MUST 先通过 `ToolRegistry` 读取工具规格，再通过 `PermissionPolicy` 产出权限决策，并通过 `ApprovalGate` 判断是否允许继续执行。`ToolRegistry` MUST NOT 提供独立 allow/deny gate；权限状态和拒绝原因 MUST 由 `PermissionPolicy` 统一产出。校验、拒绝或审批等待失败时 MUST NOT 调用 `ToolExecutor.search_code`。

`ToolSpec` MUST 包含 `requires_approval` 字段。默认 `search_code` MUST 是只读、低风险且不需要审批。

#### Scenario: 低风险只读工具直接允许执行

- **WHEN** `search_code` 已注册、只读、风险等级为 `low` 且 `requires_approval` 为 `False`
- **THEN** `PermissionPolicy` 返回 `allow`
- **AND** `AgentLoop` 调用 `ToolExecutor.search_code`
- **AND** trace events 顺序为 `request_routed`、`permission_checked`、`tool_call`、`tool_result`
- **AND** `related_files` 只包含相对仓库路径

#### Scenario: 不安全工具被拒绝

- **WHEN** 工具未注册、不是只读、或风险等级不是 `low`
- **THEN** `PermissionPolicy` 返回 `deny`
- **AND** `AgentLoop` 不调用 `ToolExecutor.search_code`
- **AND** `answer` 为 `仓库工具未通过权限策略校验，因此本次没有执行仓库工具。`
- **AND** `related_files` 为空列表
- **AND** `tool_calls` 为空列表
- **AND** trace events 顺序为 `request_routed`、`permission_checked`、`tool_rejected`

#### Scenario: 需要审批的低风险只读工具进入审批等待

- **WHEN** 工具已注册、只读、风险等级为 `low` 且 `requires_approval` 为 `True`
- **THEN** `PermissionPolicy` 返回 `ask`
- **AND** `ApprovalGate` 阻止工具执行
- **AND** `AgentLoop` 不调用 `ToolExecutor.search_code`
- **AND** `answer` 为 `工具调用需要人工审批，因此本次没有执行仓库工具。`
- **AND** `related_files` 为空列表
- **AND** `tool_calls` 为空列表
- **AND** trace events 顺序为 `request_routed`、`permission_checked`、`approval_required`

#### Scenario: 非低风险优先于审批

- **WHEN** 工具风险等级不是 `low` 且 `requires_approval` 为 `True`
- **THEN** `PermissionPolicy` 返回 `deny`
- **AND** 系统 MUST NOT 将该工具降级为 `ask`

### Requirement: Kernel 记录内部权限和审批 trace events

系统 SHALL 为 Kernel 执行过程记录结构化 trace events。V7 的权限和审批审计事件仅记录在内部 `trace_events_internal`，MUST NOT 作为 `/chat` 顶层字段暴露。Trace summary MUST 是脱敏摘要，MUST NOT 包含完整文件内容或本机绝对路径。

`AgentLoop` SHALL 负责记录 `permission_checked`、`tool_rejected` 和 `approval_required` 事件。`ApprovalGate` MUST NOT 自行记录 trace event。

#### Scenario: chat_only 不进入权限链路

- **WHEN** Kernel 将请求路由为 `chat_only`
- **THEN** trace events 仅包含 `request_routed`
- **AND** trace events MUST NOT 包含 `permission_checked`
- **AND** `related_files` 为空列表
- **AND** `tool_calls` 为空列表

### Requirement: Agent Loop 不包含未来高风险能力

当前 Agent Loop MUST NOT 修改代码、执行 shell 命令、执行 skill、使用真实 LLM、使用 RAG、使用 Memory、实现 SessionStore、执行 Reflection、运行 eval、使用复杂多 Agent 编排或实现 SandboxRunner。

#### Scenario: 当前聊天行为

- **WHEN** 用户发送聊天请求
- **THEN** 系统只执行当前确定性路由、权限边界和只读仓库搜索行为
