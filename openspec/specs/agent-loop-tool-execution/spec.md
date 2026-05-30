# agent-loop-tool-execution Specification

## Purpose

记录已实现的轻量 Agent Harness Kernel、确定性 Agent Loop、工具执行边界、V11 grounded answer 边界、V12 deterministic rewrite/rerank 边界和 V13 Memory 边界：`CodeAgent` 通过 `AgentLoop` 编排 `RequestRouter`、`MemoryManager`、`QueryUnderstanding`、`ToolRegistry`、`PermissionPolicy`、`ApprovalGate`、`ToolExecutor`、`GroundedAnswerGenerator` 和内存级 `TraceEvent`，从 repo-local hybrid RAG 结果生成 `related_files`、安全 `tool_calls` 摘要和基于证据的 `answer`。默认路径不依赖真实 LLM；显式配置后可通过 Model Provider Boundary 调用 OpenAI-compatible provider 生成 grounded answer。不修改代码、不执行 shell、不引入真实外部 embedding 服务、外部向量库、LLM query rewrite、LLM rerank、向量 Memory、自动 memory 总结、Reflection、eval、SandboxRunner 或复杂多 Agent。
## Requirements
### Requirement: Agent Loop 由轻量 Harness Kernel 编排

系统 SHALL 提供轻量 Agent Harness Kernel，用于编排请求路由、Long Task 边界、Memory 边界、工具元数据、工具调用、grounded answer 边界和 trace event。默认 Kernel MUST 保持确定性，MUST NOT 在未显式配置 provider 时依赖真实 LLM。

Long Task 指令解析 MUST 优先于 `RequestRouter` / keyword 路由，并与 V13 memory command 同级前置处理。前置控制命令的具体顺序为：先解析 V13 memory command，再解析 Long Task command，最后才进入 `RequestRouter`。Long Task 控制命令命中后，系统 MUST NOT 先执行 repo_search 或 keyword extraction。Long Task 的显式 resume/run MAY 调用当前 step action，但该 action MUST 继续通过 ToolRegistry、PermissionPolicy、ApprovalGate 和 ToolExecutor。

#### Scenario: Long Task 控制命令不进入 repo_search

- **WHEN** 聊天消息是明确 Long Task 控制命令，例如 `查看任务 task_20260529_ab12`
- **THEN** AgentLoop 在 RequestRouter 前处理该命令
- **AND** Agent MUST NOT 因 `task_20260529_ab12` 触发 repo_rag
- **AND** `related_files` 和 `tool_calls` 均为空

#### Scenario: Memory command 同级前置且先于 Long Task command

- **WHEN** 聊天消息是明确 memory command 且正文包含 `创建长任务` 或 `task_xxx`
- **THEN** AgentLoop 在 RequestRouter 前按 memory command 处理
- **AND** Agent MUST NOT 创建 Long Task
- **AND** Agent MUST NOT 执行 repo_rag

### Requirement: 工具调用经过 ToolRegistry、PermissionPolicy、ApprovalGate 和 ToolExecutor

系统 SHALL 使用 `ToolRegistry` 记录工具规格元数据，并且 repo-local 检索 MUST 继续通过统一 `ToolExecutor` 边界执行。`ToolRegistry` MUST NOT 负责实际 dispatch。

`AgentLoop` 调用工具前 MUST 先通过 `ToolRegistry` 读取工具规格，再通过 `PermissionPolicy` 产出权限决策，并通过 `ApprovalGate` 判断是否允许继续执行。`ToolRegistry` MUST NOT 提供独立 allow/deny gate；权限状态和拒绝原因 MUST 由 `PermissionPolicy` 统一产出。校验、拒绝或审批等待失败时 MUST NOT 执行 repo 检索。

`ToolSpec` MUST 包含 `requires_approval` 字段。默认 `repo_rag` MUST 是只读、低风险且不需要审批。

`AgentLoop` 在允许执行后 SHALL 使用 Query Understanding 产生的 `SearchPlan` 执行 repo-local hybrid RAG。repo-local hybrid RAG 的 `tool_calls[].tool_name` MUST 为 `repo_rag`，并且 `tool_calls` MUST 继续返回结构化审计摘要，但 MUST NOT 包含完整文件内容、本机绝对路径或新的 `/chat` 顶层 trace 字段。

#### Scenario: 注册 repo_rag 工具

- **WHEN** Kernel 初始化默认工具
- **THEN** `ToolRegistry` 包含 `repo_rag` 工具规格
- **AND** 该工具标记为只读
- **AND** 该工具风险等级为 `low`
- **AND** 该工具标记为不需要审批

#### Scenario: 低风险只读工具直接允许执行

- **WHEN** `repo_rag` 已注册、只读、风险等级为 `low` 且 `requires_approval` 为 `False`
- **THEN** `PermissionPolicy` 返回 `allow`
- **AND** `AgentLoop` 执行 query understanding 和 hybrid repo RAG
- **AND** trace events 顺序为 `request_routed`、`permission_checked`、`tool_call`、`tool_result`
- **AND** `related_files` 只包含相对仓库路径
- **AND** `tool_calls` 中的 hybrid repo RAG 审计条目使用 `tool_name=repo_rag`

#### Scenario: 不安全工具被拒绝

- **WHEN** 工具未注册、不是只读、或风险等级不是 `low`
- **THEN** `PermissionPolicy` 返回 `deny`
- **THEN** Kernel 不执行 repo 检索
- **AND** `answer` 为 `仓库工具未通过权限策略校验，因此本次没有执行仓库工具。`
- **AND** `related_files` 为空列表
- **AND** `tool_calls` 为空列表
- **AND** trace events 顺序为 `request_routed`、`permission_checked`、`tool_rejected`

#### Scenario: 需要审批的低风险只读工具进入审批等待

- **WHEN** 工具已注册、只读、风险等级为 `low` 且 `requires_approval` 为 `True`
- **THEN** `PermissionPolicy` 返回 `ask`
- **AND** `ApprovalGate` 阻止工具执行
- **AND** `AgentLoop` 不执行 repo 检索
- **AND** `answer` 为 `工具调用需要人工审批，因此本次没有执行仓库工具。`
- **AND** `related_files` 为空列表
- **AND** `tool_calls` 为空列表
- **AND** trace events 顺序为 `request_routed`、`permission_checked`、`approval_required`

#### Scenario: 非低风险优先于审批

- **WHEN** 工具风险等级不是 `low` 且 `requires_approval` 为 `True`
- **THEN** `PermissionPolicy` 返回 `deny`
- **AND** 系统 MUST NOT 将该工具降级为 `ask`

### Requirement: 聊天响应从真实搜索结果生成 related_files

系统 SHALL 从安全搜索结果填充 `related_files`，并在无命中时保持响应稳定。`related_files` MUST 只包含相对仓库路径；如果上游工具异常返回本机绝对路径，Kernel MUST 跳过该路径，避免通过 `/chat` 泄露。

#### Scenario: 搜索命中

- **WHEN** 安全仓库搜索找到匹配文件
- **THEN** `/chat` 在 `related_files` 中返回去重后的相对文件路径

#### Scenario: 搜索无命中

- **WHEN** 安全仓库搜索没有找到匹配文件
- **THEN** `/chat` 返回空 `related_files` 列表且响应仍成功

### Requirement: 工具调用摘要安全

系统 SHALL 返回包含工具名、参数摘要、状态和结果数量的工具调用摘要，并且 MUST NOT 泄露完整文件内容、完整搜索结果或本机绝对路径。

#### Scenario: repo-local hybrid RAG 调用摘要

- **WHEN** `/chat` 调用仓库搜索
- **THEN** `tool_calls` 包含 `repo_rag` 摘要、关键词、问题类型、检索模式、状态和结果数量
- **AND** 摘要不包含完整文件内容或本机绝对路径

### Requirement: Kernel 记录轻量 trace events

系统 SHALL 为 Kernel 执行过程记录结构化 trace events，至少包含路由和工具调用相关事件。当前 trace events 是内存级执行记录，不是持久化审计系统。Trace summary MUST 是脱敏摘要，MUST NOT 包含完整文件内容或本机绝对路径。

V7 的权限和审批审计事件仅记录在内部 `trace_events_internal`，MUST NOT 作为 `/chat` 顶层字段暴露。`AgentLoop` SHALL 负责记录 `permission_checked`、`tool_rejected` 和 `approval_required` 事件。`ApprovalGate` MUST NOT 自行记录 trace event。

#### Scenario: repo_search trace

- **WHEN** Kernel 执行仓库搜索
- **THEN** trace events 包含 `request_routed`
- **AND** trace events 包含 `permission_checked`
- **AND** trace events 包含 `tool_call`
- **AND** trace events 包含 `tool_result`

#### Scenario: chat_only 不进入权限链路

- **WHEN** Kernel 将请求路由为 `chat_only`
- **THEN** trace events 仅包含 `request_routed`
- **AND** trace events MUST NOT 包含 `permission_checked`
- **AND** `related_files` 为空列表
- **AND** `tool_calls` 为空列表

### Requirement: Agent Loop 不包含未来高风险能力

当前 Agent Loop MUST NOT 修改代码、执行 shell 命令、执行 skill、使用真实外部 embedding 服务、使用外部向量库、执行 LLM query rewrite、执行 LLM rerank、执行向量 Memory、实现自动 LLM memory 总结、执行 Reflection、运行 eval、使用复杂多 Agent 编排或实现 SandboxRunner。

V14 SHALL 提供 Long Task Control Plane 和 ReAct trace skeleton。该能力 MUST NOT 执行后台任务、自动循环执行、自动修改代码、创建或管理 worktree、调度真实 subagents、执行 shell、运行 evaluator 或自动语义验收。

#### Scenario: Long Task resume 仍只执行只读 repo_rag

- **WHEN** 用户显式恢复 Long Task 当前 step
- **THEN** 系统 MAY 调用只读 `repo_rag`
- **AND** 系统 MUST NOT 执行 shell、写文件工具、真实 subagent 或 worktree 操作
