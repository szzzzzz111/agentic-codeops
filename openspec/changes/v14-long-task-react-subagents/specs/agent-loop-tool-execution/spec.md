# agent-loop-tool-execution Specification

## MODIFIED Requirements

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

### Requirement: Agent Loop 不包含未来高风险能力

当前 Agent Loop MUST NOT 修改代码、执行 shell 命令、执行 skill、使用真实外部 embedding 服务、使用外部向量库、执行 LLM query rewrite、执行 LLM rerank、执行向量 Memory、实现自动 LLM memory 总结、执行 Reflection、运行 eval、使用复杂多 Agent 编排或实现 SandboxRunner。

V14 SHALL 提供 Long Task Control Plane 和 ReAct trace skeleton。该能力 MUST NOT 执行后台任务、自动循环执行、自动修改代码、创建或管理 worktree、调度真实 subagents、执行 shell、运行 evaluator 或自动语义验收。

#### Scenario: Long Task resume 仍只执行只读 repo_rag

- **WHEN** 用户显式恢复 Long Task 当前 step
- **THEN** 系统 MAY 调用只读 `repo_rag`
- **AND** 系统 MUST NOT 执行 shell、写文件工具、真实 subagent 或 worktree 操作
