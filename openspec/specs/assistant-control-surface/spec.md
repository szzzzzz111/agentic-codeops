# assistant-control-surface Specification

## Purpose
定义 RepoPilot 通过现有 `/chat` 暴露的只读 Assistant Control Surface，包括状态聚合、公开回答边界、路由优先级和非写入约束。
## Requirements
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

### Requirement: 控制面状态聚合只读且不隐式初始化本地 DB

系统 SHALL 聚合 Memory 和 Long Task 的只读状态摘要。控制面状态读取 MUST NOT 创建 `.repopilot/` 目录，MUST NOT 创建 `memory.sqlite3`，MUST NOT 创建 `tasks.sqlite3`。

#### Scenario: 不存在本地状态 DB 时仍可返回状态

- **WHEN** 有效 repo_path 内不存在 `.repopilot/`
- **THEN** 控制面回答显示 Memory 和 Long Task 为空或未初始化
- **AND** 文件系统中仍不存在 `.repopilot/` 目录

### Requirement: 控制面不执行检索或写入动作

系统 SHALL 把 Assistant Control Surface 作为只读分支。控制面请求 MUST NOT 调用 `repo_rag`，MUST NOT 写入 memory，MUST NOT 创建、恢复、暂停、补充或归档 Long Task。

#### Scenario: 控制面请求不调用工具

- **WHEN** 用户发送 `助手状态`
- **THEN** AgentLoop MUST NOT 执行 `repo_rag`
- **AND** AgentLoop MUST NOT 进入 PermissionPolicy / ApprovalGate 工具调用链路

### Requirement: 控制面回答脱敏

系统 SHALL 对控制面回答进行脱敏。公开 `answer` MUST NOT 包含完整 memory value、完整 scratch、完整 ReAct trace、完整 Evidence Pack、完整 provider output、本机绝对路径或 DB 路径。

#### Scenario: 控制面不泄露本地路径或内部状态

- **WHEN** 控制面读取 Memory 和 Long Task 摘要
- **THEN** `answer` MAY 包含 memory 计数、任务数量、task_id、任务状态、任务标题和下一步标题
- **AND** `answer` MUST NOT 包含本机绝对路径、`memory.sqlite3`、`tasks.sqlite3`、scratch 正文或 provider output

### Requirement: 控制面路由优先级稳定

系统 SHALL 在 AgentLoop 中按固定顺序处理前置控制面：Memory command、Long Task command、Assistant Control Surface，然后进入 `RequestRouter` 的 capability_status / repo_search / chat_only routing。

Assistant Control Surface status parsing SHALL remain narrow and explicit. Cleanup of capability-status routing or test names MUST NOT add new status trigger phrases unless a separate behavior-expansion change explicitly approves them.

#### Scenario: Memory 和 Long Task 命令优先于控制面

- **WHEN** 用户发送明确 memory command 或 Long Task command，且正文包含助手状态类词语
- **THEN** 系统 MUST 按 Memory 或 Long Task 命令处理
- **AND** 系统 MUST NOT 返回 Assistant Control Surface 状态回答

#### Scenario: capability-status 不被控制面误吞

- **WHEN** 用户发送 `memory 实现了吗?`
- **THEN** 系统 MUST 返回 capability-status 回答
- **AND** 系统 MUST NOT 返回 Assistant Control Surface 聚合状态

#### Scenario: 控制面 cleanup 不扩展自然语言触发词

- **WHEN** 用户发送未列入明确状态触发词的普通自然语言问题
- **THEN** Assistant Control Surface parser MUST NOT classify it as a status request
- **AND** the request MAY continue to normal routing

