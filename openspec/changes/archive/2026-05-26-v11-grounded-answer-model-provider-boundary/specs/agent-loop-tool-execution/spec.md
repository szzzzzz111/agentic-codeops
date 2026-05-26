# agent-loop-tool-execution Specification

## MODIFIED Requirements

### Requirement: Agent Loop 由轻量 Harness Kernel 编排

系统 SHALL 提供轻量 Agent Harness Kernel，用于编排请求路由、工具元数据、工具调用、grounded answer 边界和 trace event。默认 Kernel MUST 保持确定性，MUST NOT 在未显式配置 provider 时依赖真实 LLM。V11 MAY 通过 Model Provider Boundary 在显式配置下调用真实 OpenAI-compatible provider，但该 provider MUST NOT 绕过 AgentLoop、ToolExecutor、PermissionPolicy、ApprovalGate 或 Evidence Pack / Context Budget 边界。

Kernel MUST 定义最小可测试 contract：`AgentLoopRequest(message, repo_path, trace_id)`、`RouteDecision(route, keyword, reason)`、`ToolSpec(name, description, read_only, risk, requires_approval)`、`PermissionDecision(tool_name, status, reason)`、`TraceEvent(event_type, tool_name, status, summary)` 和内部 `AgentLoopResult(answer, related_files, tool_calls, trace_events_internal)`。

#### Scenario: 可搜索请求进入 repo_search route

- **WHEN** 聊天消息包含明确可搜索 token，例如 `UNIQUE_BUG_TOKEN`
- **THEN** Kernel 将请求路由为 `repo_search`
- **AND** route decision 包含搜索 keyword 和路由原因
- **AND** Agent 通过注册工具执行仓库搜索
- **AND** Agent MAY 在 successful evidence pack 后通过 grounded answer 边界生成回答

#### Scenario: 不含搜索 token 的请求进入 chat_only route

- **WHEN** 聊天消息不包含可搜索 token
- **THEN** Kernel 将请求路由为 `chat_only`
- **AND** route decision 不包含搜索 keyword
- **AND** Agent 不调用仓库搜索工具

### Requirement: Agent Loop 不包含未来高风险能力

当前 Agent Loop MUST NOT 修改代码、执行 shell 命令、执行 skill、使用真实外部 embedding 服务、使用外部向量库、执行 LLM query rewrite、执行 LLM rerank、使用 Memory、实现 SessionStore、执行 Reflection、运行 eval、使用复杂多 Agent 编排或实现 SandboxRunner。

V11 MAY 在显式配置下通过 Model Provider Boundary 调用 OpenAI-compatible provider 生成 grounded answer。该 provider MUST 只消费预算内 evidence，不得参与检索规划、工具调用、代码修改、query rewrite、rerank、memory 或多步 agent 决策。

#### Scenario: 当前聊天行为

- **WHEN** 用户发送聊天请求
- **THEN** 系统只执行当前确定性路由、权限边界、只读仓库搜索和 grounded answer 边界行为
- **AND** 系统 MUST NOT 执行代码修改、shell、skill、memory、rerank 或多 agent 编排
