# agent-loop-tool-execution Specification

## MODIFIED Requirements

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

### Requirement: Agent Loop 不包含未来高风险能力

当前 Agent Loop MUST NOT 执行 shell 命令、执行 skill、使用真实外部 embedding 服务、使用外部向量库、执行 LLM query rewrite、执行 LLM rerank、执行向量 Memory、实现自动 LLM memory 总结、执行 Reflection、运行 eval、使用复杂多 Agent 编排或实现 SandboxRunner。

V16 SHALL 提供 Safe Patch Authoring。该能力 MAY 在明确确认后通过 `patch_apply` 修改 unified diff 中的目标文件，但 MUST NOT 运行测试命令、自动 commit、创建或管理 worktree、调度真实 subagents、执行后台任务或自动循环执行。

#### Scenario: V16 不执行验证或 git 操作

- **WHEN** 用户确认应用 patch
- **THEN** 系统 MAY 修改 diff 目标文件
- **AND** 系统 MUST NOT 运行测试、commit、push 或创建 worktree
