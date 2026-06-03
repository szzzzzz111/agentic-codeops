## MODIFIED Requirements

### Requirement: Agent Loop 由轻量 Harness Kernel 编排

系统 SHALL 提供轻量 Agent Harness Kernel，用于编排请求路由、Long Task 边界、Memory 边界、Assistant Control Surface、Patch command / Patch intent、Verification intent、工具元数据、工具调用、grounded answer 边界和 trace event。默认 Kernel MUST 保持确定性，MUST NOT 在未显式配置 provider 时依赖真实 LLM。

前置控制命令的具体顺序为：先解析 V13 memory command，再解析 Long Task command，然后解析 Assistant Control Surface 状态请求，然后解析 V16 Patch command / Patch intent，然后解析 V17 Verification intent，最后才进入 capability-status 或 `RequestRouter`。Patch command / Patch intent 和 Verification intent 命中后，系统 MUST NOT 将该请求误当作普通 repo_search 或 capability-status。

#### Scenario: Verification intent 在 repo_search 前处理

- **WHEN** 聊天消息是明确验证请求
- **THEN** AgentLoop 在 capability-status 和 repo_search 前处理该请求
- **AND** Agent MUST NOT 直接走普通 repo_search answer

#### Scenario: Memory、Long Task、Assistant Control Surface 和 Patch 仍优先于 Verification

- **WHEN** 聊天消息是明确 memory command、Long Task command、Assistant Control Surface 请求或 Patch command / Patch intent
- **THEN** AgentLoop MUST 先按既有前置分支处理
- **AND** Agent MUST NOT 因正文包含 verify 或 test 词而改走 Verification intent

### Requirement: 工具调用经过 ToolRegistry、PermissionPolicy、ApprovalGate 和 ToolExecutor

系统 SHALL 使用 `ToolRegistry` 记录工具规格元数据，并且 repo-local 检索、V16 patch apply 和 V17 verification run MUST 继续通过统一 `ToolExecutor` 边界执行。`ToolRegistry` MUST NOT 负责实际 dispatch。

`PermissionPolicy` MUST 继续只产出 `allow`、`deny` 或 `ask`。系统 SHALL 使用可选 `ToolInvocationContext`，使 `PermissionPolicy.decide(tool_spec, tool_name, context=None)` 和 `ApprovalGate.evaluate(decision, context=None)` 能消费已归一化的工具调用上下文。现有只读工具调用在未传 context 时 MUST 保持兼容。

`verification_run` MUST 注册为 `read_only=False`、`risk="write"`、`requires_approval=True` 的高风险工具。`verification_run` 只有在有效 verification context 下 MAY 由 `PermissionPolicy` 返回 `ask`，并由 `ApprovalGate` 判定通过。有效 context MUST 只携带归一化验证标签和 repo scope，不携带用户原始 shell 命令。非白名单命令、缺少有效 context、repo scope 无效或命令标签不匹配时 MUST 返回 `deny`。普通非 low 风险工具仍 MUST 按既有策略拒绝。

#### Scenario: verification_run 在有效上下文下通过审批

- **WHEN** `verification_run` 已注册且 `ToolInvocationContext` 表示白名单标签有效且 repo scope 有效
- **THEN** `PermissionPolicy` 返回 `ask`
- **AND** `ApprovalGate` 判定通过
- **AND** AgentLoop MAY 调用 `ToolExecutor.verification_run`

#### Scenario: verification_run 在无效上下文下被拒绝

- **WHEN** `verification_run` 缺少有效 verification context
- **THEN** `PermissionPolicy` 返回 `deny`
- **AND** AgentLoop MUST NOT 调用 `ToolExecutor.verification_run`

### Requirement: Agent Loop 不包含未来高风险能力

当前 Agent Loop MUST NOT 执行任意 shell 命令、执行 skill、使用真实外部 embedding 服务、使用外部向量库、执行 LLM query rewrite、执行 LLM rerank、执行向量 Memory、实现自动 LLM memory 总结、执行 Reflection、运行 eval、使用复杂多 Agent 编排或实现 SandboxRunner。

V17 SHALL 提供 Verification Runner。该能力 MAY 在明确验证请求和有效白名单上下文下运行 `pytest`、`ruff check .` 或 `scripts/verify.ps1`，但 MUST NOT 接受任意 shell、自动在 patch apply 后运行验证、根据验证失败自动生成 patch、持久化验证结果、commit、push、创建或管理 worktree、调度真实 subagents、执行后台任务或自动循环执行。

#### Scenario: V17 不执行 patch verify loop 或 git 操作

- **WHEN** 用户运行明确验证请求
- **THEN** 系统 MAY 执行白名单验证命令
- **AND** 系统 MUST NOT 自动生成 patch、commit、push 或创建 worktree
