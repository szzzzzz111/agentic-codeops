## Current Behavior

当前 `/chat` 链路为 `ChatService -> CodeAgent -> ToolExecutor -> search_code`。`CodeAgent` 同时承担关键词提取、简单决策、工具调用编排和响应组织。V4/V5 的 skill loader 已存在，但当前不应作为 V6 主目标继续扩展。

## Target Behavior

V6 建立一个更窄的轻量 Agent Harness Kernel，只做当前搜索链路的工程化包裹：

- `RequestRouter`：把请求路由到 `chat_only` 或 `repo_search`，为后续 RAG、Memory、ReAct 留入口。
- `ToolRegistry`：记录工具规格元数据，包括工具名、说明、只读标记和风险等级；本阶段不负责 dispatch，但 `AgentLoop` 调用工具前 MUST 先通过 `ToolRegistry` 确认工具存在、只读且风险等级允许。
- `AgentLoop`：执行最小 loop：route -> optional `ToolExecutor.search_code` -> result -> response。
- `TraceEvent`：记录 `request_routed`、`tool_call`、`tool_result` 等结构化内存事件。

Provider、Context、Skill 和 Session 只作为后续扩展方向记录在路线中，不在 V6 实现运行时骨架，避免单阶段抽象过多。

`CodeAgent` 调用 Kernel 后继续返回 `AgentResult(answer, related_files, tool_calls)`，因此 `/chat` API schema 不变。

## Minimal Contracts

V6 的 Kernel contract 必须足够小，但要可测试、可替换：

- `AgentLoopRequest(message, repo_path, trace_id)`：
  - `message` 是用户输入。
  - `repo_path` 是当前请求的仓库路径，实际文件访问仍交给 `ToolExecutor` 和安全文件工具。
  - `trace_id` 是 `ChatService` 生成的请求级 trace id。
- `RouteDecision(route, keyword, reason)`：
  - `route` 只能是 `chat_only` 或 `repo_search`。
  - `keyword` 是可选搜索关键词；`chat_only` 时为空。
  - `reason` 记录路由原因，用于 trace 摘要。
- `ToolSpec(name, description, read_only, risk)`：
  - `name` 是工具名，例如 `search_code`。
  - `description` 是面向审计和 review 的简短说明。
  - `read_only` 必须标记工具是否只读。
  - `risk` 使用轻量字符串等级，V6 默认只允许 `low`。
- `TraceEvent(event_type, tool_name, status, summary)`：
  - `event_type` 至少支持 `request_routed`、`tool_call`、`tool_result`。
  - `tool_name` 在非工具事件中可以为空。
  - `status` 记录 `ok` 或 `error`。
  - `summary` 必须是脱敏摘要，不包含完整文件内容或本机绝对路径。
- `AgentLoopResult(answer, related_files, tool_calls, trace_events_internal)`：
  - `answer`、`related_files`、`tool_calls` 用于适配现有 `AgentResult`。
  - `trace_events_internal` 仅供内部测试和后续审计演进，不作为 `/chat` 顶层字段返回。

## Tool Boundary Gate

V6 的 `ToolRegistry` 不是运行时 dispatch 层，但必须成为工具调用前的边界声明源：

- `AgentLoop` 在执行 `repo_search` 时，先读取 `search_code` 的 `ToolSpec`。
- 如果工具不存在、不是只读、或风险等级不是 V6 允许值，`AgentLoop` MUST NOT 调用 `ToolExecutor.search_code`。
- registry gate 拒绝时，`TraceEvent.summary` 应记录稳定原因：`not_registered`、`not_read_only` 或 `risk_not_allowed`。
- 通过校验后，实际仓库搜索仍 MUST 经由 `ToolExecutor.search_code`，不得绕过既有安全文件工具。
- 工具拒绝和工具错误都应进入 `TraceEvent`，但 `/chat` 顶层响应结构保持不变。

## Non-goals

- 不接真实 LLM。
- 不执行 skill。
- 不做 RAG、Memory、Reflection、eval 或复杂多 Agent。
- 不实现 `ProviderAdapter`、`ContextBuilder`、`SkillRegistry` 或 `SessionStore` 的运行时代码。
- 不新增写文件、删文件、shell 执行能力。
- 不实现 PermissionPolicy、ApprovalGate 或 SandboxRunner。
- 不引入 PostgreSQL、Milvus、Elasticsearch、Kafka 等重依赖。
- 不新增 `/chat` 顶层响应字段。

## Data Returned and Not Returned

返回：

- `answer`：继续使用当前中文回答。
- `related_files`：继续从 `search_code` 结果中去重生成。
- `tool_calls`：继续返回安全工具调用摘要。

不返回：

- 完整文件内容。
- 本机绝对路径。
- trace events 顶层字段。
- session / memory 内部状态。

## Error Behavior

- 工具错误继续由 `ToolExecutor` 脱敏为错误类型。
- Kernel trace 记录错误事件，但 `/chat` 响应仍保持当前成功返回语义。
- Router 无法识别可搜索 token 时走 `chat_only`，不调用仓库工具，并保持当前“未提取到可搜索关键词，因此没有调用仓库工具。”回答语义。

## Security and Boundaries

- 运行时仓库搜索必须继续经过 `ToolExecutor`。
- Kernel 只建立可替换接口，不绕过现有安全文件工具。
- 高风险能力仍必须在后续阶段经 Permission/Approval/Sandbox 设计后开放。

## Engineering Taste

本阶段体现轻量工程化：用接口、trace、测试和文档边界建立演进空间；默认实现保持内存级和确定性，不引入个人维护不起的基础设施。
