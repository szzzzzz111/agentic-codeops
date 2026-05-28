# agent-loop-tool-execution Specification

## MODIFIED Requirements

### Requirement: Agent Loop 由轻量 Harness Kernel 编排

系统 SHALL 提供轻量 Agent Harness Kernel，用于编排请求路由、Memory 边界、工具元数据、工具调用、grounded answer 边界和 trace event。默认 Kernel MUST 保持确定性，MUST NOT 在未显式配置 provider 时依赖真实 LLM。V11 MAY 通过 Model Provider Boundary 在显式配置下调用真实 OpenAI-compatible provider，但该 provider MUST NOT 绕过 AgentLoop、ToolExecutor、PermissionPolicy、ApprovalGate、Memory audit 或 Evidence Pack / Context Budget 边界。

Kernel MUST 定义最小可测试 contract：`AgentLoopRequest(message, repo_path, trace_id, user_id, session_id)`、`RouteDecision(route, keyword, reason)`、`ToolSpec(name, description, read_only, risk, requires_approval)`、`PermissionDecision(tool_name, status, reason)`、`TraceEvent(event_type, tool_name, status, summary)` 和内部 `AgentLoopResult(answer, related_files, tool_calls, trace_events_internal)`。

V12 SHALL 在 repo_search 链路中记录 deterministic query rewrite 和 rerank 的内部 trace summary。V13 SHALL 在 memory command 或普通请求 memory read 时记录内部 memory trace summary。该 summary MUST NOT 作为 `/chat` 顶层字段暴露，也 MUST NOT 将完整 memory value、完整 variants、完整 retrieval results、完整 Evidence Pack、本机绝对路径或模型输出写入 `/chat.tool_calls`。

#### Scenario: memory command 确认优先

- **WHEN** 聊天消息是明确 memory command
- **THEN** Kernel 处理 memory command 并返回确认式 answer
- **AND** Agent MUST NOT 调用 repo_rag
- **AND** `related_files` 和 `tool_calls` 均为空

#### Scenario: 普通 repo_search 记录 memory summary

- **WHEN** 聊天消息进入 repo_search
- **THEN** Kernel MAY 读取 memory 并记录脱敏 memory summary
- **AND** Kernel 继续通过权限、审批和 ToolExecutor 执行 repo_rag
- **AND** `/chat.tool_calls` MUST NOT 包含 memory 内容

### Requirement: Agent Loop 不包含未来高风险能力

当前 Agent Loop MUST NOT 修改代码、执行 shell 命令、执行 skill、使用真实外部 embedding 服务、使用外部向量库、执行 LLM query rewrite、执行 LLM rerank、执行向量 Memory、实现自动 LLM memory 总结、执行 Reflection、运行 eval、使用复杂多 Agent 编排或实现 SandboxRunner。

V11 MAY 在显式配置下通过 Model Provider Boundary 调用 OpenAI-compatible provider 生成 grounded answer。该 provider MUST 只消费预算内 evidence，不得参与检索规划、工具调用、代码修改、query rewrite、rerank、memory 写入或多步 agent 决策。

V12 SHALL 提供默认 deterministic query rewrite 和 deterministic rerank。该能力 MUST NOT 调用真实 LLM，MUST NOT 改变权限/审批边界，MUST NOT 修改代码或执行 shell。

V13 SHALL 提供 repo-local SQLite-backed PREF/LTM、进程内 STM、明确 memory 指令和内部 memory audit。该能力 MUST NOT 执行向量召回、自动模型总结、context compression、代码修改或 shell。

#### Scenario: 当前聊天行为

- **WHEN** 用户发送聊天请求
- **THEN** 系统只执行当前确定性路由、Memory 指令/读取、权限边界、只读仓库搜索、deterministic rewrite/rerank 和 grounded answer 边界行为
- **AND** 系统 MUST NOT 执行代码修改、shell、skill、向量 memory、LLM rewrite/rerank 或多 agent 编排
