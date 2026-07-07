## MODIFIED Requirements

### Requirement: 系统通过 `/chat` 提供只读助手控制面

系统 SHALL 通过现有 `POST /chat` 提供 Assistant Control Surface。控制面请求 MUST 使用现有 `/chat.answer` 返回状态说明，MUST NOT 新增 API，MUST NOT 新增 `/chat` 顶层响应字段。

Assistant Control Surface 的当前能力摘要 MUST 复用与 capability-status 相同 adapter 产出的 structured runtime-derived capability facts，而不是维护独立静态能力文案。控制面可以用不同 formatter 输出这些事实：它 MUST keep the existing concise affirmative style and MUST NOT dump stage-versioned capability-status paragraphs into the generic status answer.

When Assistant Control Surface is invoked from `AgentLoop`, the capability facts MUST be derived from that loop's active `ToolRegistry` or from an explicitly passed summary generated from that registry. It MUST NOT silently fall back to a default registry that differs from the active loop registry.

#### Scenario: 明确助手状态请求返回控制面回答

- **WHEN** 用户发送 `助手状态`、`RepoPilot 状态`、`你能做什么`、`assistant status` 或 `what can you do`
- **THEN** 系统返回包含当前能力、当前本地状态和下一步命令建议的 `answer`
- **AND** 当前能力段来自 runtime-derived structured capability facts
- **AND** 当前能力段保持简短，MUST NOT include stage-version markers such as `V11`, `V12`, `V13`, `V16` or `V25`
- **AND** `related_files` 为空列表
- **AND** `tool_calls` 为空列表

#### Scenario: 控制面不把开发流程说成 runtime 能力

- **WHEN** 控制面回答当前能力
- **THEN** 回答 MUST NOT claim RepoPilot currently exposes an MCP server, executes skills, runs connectors or dispatches runtime subagents
- **AND** 回答 SHOULD avoid introducing technology denial clauses such as MCP, Skill execution, connector or runtime subagent in the generic status answer unless a separate approved change expands that wording

#### Scenario: 控制面使用 active ToolRegistry 派生事实

- **WHEN** AgentLoop 使用 custom `ToolRegistry` 处理 `assistant status`
- **THEN** Assistant Control Surface 的当前能力段 MUST be derived from that active registry's capability facts
- **AND** it MUST NOT advertise execution primitives that are missing from the active registry as currently available
- **AND** `related_files` 为空列表
- **AND** `tool_calls` 为空列表
- **AND** AgentLoop MUST NOT call repo RAG
