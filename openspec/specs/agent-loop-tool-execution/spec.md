# agent-loop-tool-execution Specification

## Purpose

记录已实现的轻量 Agent Harness Kernel、确定性 Agent Loop、工具执行边界、V11 grounded answer 边界、V12 deterministic rewrite/rerank 边界和 V13 Memory 边界：`CodeAgent` 通过 `AgentLoop` 编排 `RequestRouter`、`MemoryManager`、`QueryUnderstanding`、`ToolRegistry`、`PermissionPolicy`、`ApprovalGate`、`ToolExecutor`、`GroundedAnswerGenerator` 和内存级 `TraceEvent`，从 repo-local hybrid RAG 结果生成 `related_files`、安全 `tool_calls` 摘要和基于证据的 `answer`。默认路径不依赖真实 LLM；显式配置后可通过 Model Provider Boundary 调用 OpenAI-compatible provider 生成 grounded answer。不修改代码、不执行 shell、不引入真实外部 embedding 服务、外部向量库、LLM query rewrite、LLM rerank、向量 Memory、自动 memory 总结、Reflection、eval、SandboxRunner 或复杂多 Agent。
## Requirements
### Requirement: Agent Loop 由轻量 Harness Kernel 编排

系统 SHALL 提供轻量 Agent Harness Kernel，用于编排请求路由、Long Task 边界、Memory 边界、Assistant Control Surface、Patch command / Patch intent、工具元数据、工具调用、grounded answer 边界和 trace event。默认 Kernel MUST 保持确定性，MUST NOT 在未显式配置 provider 时依赖真实 LLM。

前置控制命令的具体顺序为：先解析 V13 memory command，再解析 Long Task command，然后解析 Assistant Control Surface 状态请求，然后解析 V16 Patch command / Patch intent，最后才进入 capability-status 或 `RequestRouter`。Patch command / Patch intent 命中后，系统 MUST NOT 将该请求误当作普通 repo_search 或 capability-status。

#### Scenario: Patch intent 在 repo_search 前处理

- **WHEN** 聊天消息是明确 patch proposal 请求
- **THEN** AgentLoop 在 capability-status 和 repo_search 前处理该请求
- **AND** Agent MUST NOT 直接走普通 repo_search answer

#### Scenario: Memory、Long Task 和 Assistant Control Surface 仍优先于 Patch

- **WHEN** 聊天消息是明确 memory command、Long Task command 或 Assistant Control Surface 请求
- **THEN** AgentLoop MUST 先按既有前置分支处理
- **AND** Agent MUST NOT 因正文包含 patch 词而改走 Patch intent

### Requirement: 工具调用经过 ToolRegistry、PermissionPolicy、ApprovalGate 和 ToolExecutor

系统 SHALL 使用 `ToolRegistry` 记录工具规格元数据，并且 repo-local 检索和 V16 patch apply MUST 继续通过统一 `ToolExecutor` 边界执行。`ToolRegistry` MUST NOT 负责实际 dispatch。

`PermissionPolicy` MUST 继续只产出 `allow`、`deny` 或 `ask`。系统 SHALL 引入可选 `ToolInvocationContext`，使 `PermissionPolicy.decide(tool_spec, tool_name, context=None)` 和 `ApprovalGate.evaluate(decision, context=None)` 能消费已归一化的工具调用上下文。现有只读工具调用在未传 context 时 MUST 保持兼容。

`patch_apply` MUST 注册为 `read_only=False`、`risk=write`、`requires_approval=True`。`patch_apply` 只有在有效确认上下文下 MAY 由 `PermissionPolicy` 返回 `ask`，并由 `ApprovalGate` 判定通过。非确认态写入、跨用户/跨 repo、hash 不匹配、状态非 pending、TTL 过期或 scope 无效时 MUST 返回 `deny`。

#### Scenario: patch_apply 在有效确认上下文下通过审批

- **WHEN** `patch_apply` 已注册且 `ToolInvocationContext` 表示 pending patch 有效、确认语法有效、scope 有效、diff hash 匹配且未过期
- **THEN** `PermissionPolicy` 返回 `ask`
- **AND** `ApprovalGate` 判定通过
- **AND** AgentLoop MAY 调用 `ToolExecutor.patch_apply`

#### Scenario: patch_apply 在无效确认上下文下被拒绝

- **WHEN** `patch_apply` 缺少有效确认上下文
- **THEN** `PermissionPolicy` 返回 `deny`
- **AND** AgentLoop MUST NOT 调用 `ToolExecutor.patch_apply`

#### Scenario: 普通 ask 仍阻止执行

- **WHEN** 非 `patch_apply` 工具返回 `ask`
- **THEN** `ApprovalGate` MUST 继续阻止执行

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

当前 Agent Loop MUST NOT 执行 shell 命令、执行 skill、使用真实外部 embedding 服务、使用外部向量库、执行 LLM query rewrite、执行 LLM rerank、执行向量 Memory、实现自动 LLM memory 总结、执行 Reflection、运行 eval、使用复杂多 Agent 编排或实现 SandboxRunner。

V16 SHALL 提供 Safe Patch Authoring。该能力 MAY 在明确确认后通过 `patch_apply` 修改 unified diff 中的目标文件，但 MUST NOT 运行测试命令、自动 commit、创建或管理 worktree、调度真实 subagents、执行后台任务或自动循环执行。

#### Scenario: V16 不执行验证或 git 操作

- **WHEN** 用户确认应用 patch
- **THEN** 系统 MAY 修改 diff 目标文件
- **AND** 系统 MUST NOT 运行测试、commit、push 或创建 worktree
