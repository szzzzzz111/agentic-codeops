# agent-loop-tool-execution Specification

## MODIFIED Requirements

### Requirement: Agent Loop 由轻量 Harness Kernel 编排

系统 SHALL 提供轻量 Agent Harness Kernel，用于编排请求路由、Long Task 边界、Memory 边界、Assistant Control Surface、工具元数据、工具调用、grounded answer 边界和 trace event。默认 Kernel MUST 保持确定性，MUST NOT 在未显式配置 provider 时依赖真实 LLM。

前置控制命令的具体顺序为：先解析 V13 memory command，再解析 Long Task command，然后解析 Assistant Control Surface 状态请求，最后才进入 capability-status 或 `RequestRouter`。Assistant Control Surface 状态请求命中后，系统 MUST NOT 执行 repo_search、keyword extraction 或 repo_rag。

#### Scenario: Assistant Control Surface 在 repo_search 前处理

- **WHEN** 聊天消息是明确助手状态请求，例如 `助手状态`
- **THEN** AgentLoop 在 repo_search 前处理该请求
- **AND** Agent MUST NOT 执行 `repo_rag`
- **AND** `related_files` 和 `tool_calls` 均为空

#### Scenario: Memory 和 Long Task 仍优先于 Assistant Control Surface

- **WHEN** 聊天消息是明确 memory command 或 Long Task command
- **THEN** AgentLoop MUST 先按既有 Memory 或 Long Task 命令处理
- **AND** Agent MUST NOT 因正文包含助手状态词而改走 Assistant Control Surface

### Requirement: Agent Loop 不包含未来高风险能力

当前 Agent Loop MUST NOT 修改代码、执行 shell 命令、执行 skill、使用真实外部 embedding 服务、使用外部向量库、执行 LLM query rewrite、执行 LLM rerank、执行向量 Memory、实现自动 LLM memory 总结、执行 Reflection、运行 eval、使用复杂多 Agent 编排或实现 SandboxRunner。

V15 SHALL 提供 Assistant Control Surface。该能力 MUST NOT 新增 API、自动修改代码、执行 shell、运行验证命令、执行后台任务、自动循环执行、创建或管理 worktree、调度真实 subagents、写入 Memory 或创建 Long Task。

#### Scenario: V15 控制面只读

- **WHEN** 用户请求助手状态
- **THEN** 系统 MAY 聚合只读 Memory 和 Long Task 摘要
- **AND** 系统 MUST NOT 写文件、执行 shell、运行验证、创建任务或调用 repo_rag
