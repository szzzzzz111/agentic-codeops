# agent-loop-tool-execution Delta

## MODIFIED Requirements

### Requirement: Agent Loop 由轻量 Harness Kernel 编排

系统 SHALL 提供轻量 Agent Harness Kernel，用于编排请求路由、工具元数据、工具调用和 trace event。当前 Kernel MUST 保持确定性，MUST NOT 依赖真实 LLM。

Kernel MUST 定义最小可测试 contract：`AgentLoopRequest(message, repo_path, trace_id)`、`RouteDecision(route, keyword, reason)`、`ToolSpec(name, description, read_only, risk)`、`TraceEvent(event_type, tool_name, status, summary)` 和内部 `AgentLoopResult(answer, related_files, tool_calls, trace_events_internal)`。

#### Scenario: 可搜索请求进入 repo_search route

- **WHEN** 聊天消息包含明确可搜索 token，例如 `UNIQUE_BUG_TOKEN`
- **THEN** Kernel 将请求路由为 `repo_search`
- **AND** route decision 包含搜索 keyword 和路由原因
- **AND** Agent 通过注册工具执行仓库搜索

#### Scenario: 不含搜索 token 的请求进入 chat_only route

- **WHEN** 聊天消息不包含可搜索 token
- **THEN** Kernel 将请求路由为 `chat_only`
- **AND** route decision 不包含搜索 keyword
- **AND** Agent 不调用仓库搜索工具

### Requirement: 工具调用经过 ToolRegistry 和 ToolExecutor

系统 SHALL 使用 `ToolRegistry` 记录工具规格元数据，并且当前仓库搜索 MUST 继续通过 `ToolExecutor.search_code` 执行。`ToolRegistry` 在 V6 MUST NOT 负责实际 dispatch。

`AgentLoop` 调用工具前 MUST 先通过 `ToolRegistry` 校验工具存在、工具为只读、风险等级在 V6 允许范围内；校验失败时 MUST NOT 调用 `ToolExecutor.search_code`。

#### Scenario: 注册 search_code 工具

- **WHEN** Kernel 初始化默认工具
- **THEN** `ToolRegistry` 包含 `search_code` 工具规格
- **AND** 该工具标记为只读
- **AND** 该工具风险等级为 `low`

#### Scenario: 执行 search_code 工具

- **WHEN** Kernel 执行 `repo_search` route
- **THEN** 它先通过 `ToolRegistry` 校验 `search_code`
- **AND** 校验通过后通过 `ToolExecutor.search_code` 调用安全仓库搜索

#### Scenario: search_code 工具未通过 registry 校验

- **WHEN** `search_code` 未注册、不是只读、或风险等级不被允许
- **THEN** Kernel 不调用 `ToolExecutor.search_code`
- **AND** Kernel 记录工具拒绝 trace event
- **AND** trace summary 记录稳定拒绝原因：`not_registered`、`not_read_only` 或 `risk_not_allowed`

### Requirement: Kernel 记录轻量 trace events

系统 SHALL 为 Kernel 执行过程记录结构化 trace events，至少包含路由和工具调用相关事件。当前 trace events 是内存级执行记录，不是持久化审计系统。Trace summary MUST 是脱敏摘要，MUST NOT 包含完整文件内容或本机绝对路径。

#### Scenario: repo_search trace

- **WHEN** Kernel 执行仓库搜索
- **THEN** trace events 包含 `request_routed`
- **AND** trace events 包含 `tool_call`
- **AND** trace events 包含 `tool_result`

### Requirement: Agent Loop 不包含未来高风险能力

当前 Agent Loop MUST NOT 修改代码、执行 shell 命令、执行 skill、使用真实 LLM、使用 RAG、使用 Memory、实现 SessionStore、执行 Reflection、运行 eval 或使用复杂多 Agent 编排。

#### Scenario: 当前聊天行为

- **WHEN** 用户发送聊天请求
- **THEN** 系统只执行当前确定性路由和只读仓库搜索行为
