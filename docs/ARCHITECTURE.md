# 架构说明

RepoPilot 当前采用渐进式 Harness 架构。目标不是替代通用 AI IDE 或 AI 编程助手，而是围绕代码仓库分析任务，把 Agent 的工具调用、安全边界、执行追踪、验证和交接机制做成可控、可审计、可扩展的执行框架。

## 当前主链路

```text
API -> ChatService(trace_id) -> CodeAgent -> AgentLoop -> ToolRegistry -> PermissionPolicy -> ApprovalGate -> ToolExecutor -> file_tools
```

- API 层只接收请求并返回响应。
- `ChatService` 负责编排请求、生成 `trace_id`、调用智能体。
- `CodeAgent` 负责最小确定性关键词提取、组织工具调用和返回结果。
- `ToolExecutor` 统一收口工具执行，当前只包装只读 `search_code`。
- `file_tools` 提供安全仓库文件工具，不处理 HTTP 或 Agent 决策。
- Trace 贯穿请求生命周期，由 `ChatService` 创建请求级唯一 `trace_id`，并随 `/chat` 响应返回。当前 Trace 仍是请求级标识，不是完整持久化审计系统；后续可扩展工具调用审计。

V3 当前已经让 `/chat` 返回真实 `related_files` 和 `tool_calls`，但仍不接真实 LLM、不自动修改代码、不执行 shell。

## V2 工具层：安全只读仓库能力

V2 新增安全只读文件工具：

```text
app/tools/file_tools.py
```

包含：

- `list_files(repo_path)`
- `read_file(repo_path, file_path, max_chars=12000)`
- `search_code(repo_path, keyword, max_results=20)`

这些工具限制访问在 `repo_path` 内，拒绝路径逃逸，跳过敏感文件、隐藏目录、忽略目录和二进制文件。V3 当前已经通过 `ToolExecutor` 把 `search_code` 接入 `/chat`。

## V3 执行层：ToolExecutor

V3 新增：

```text
app/tools/tool_executor.py
```

当前职责：

- 调用 `search_code`。
- 捕获工具错误并返回结构化摘要。
- 生成 `tool_calls` 所需的工具名称、关键词、状态和结果数量。
- 不返回完整文件内容、完整搜索结果或本机绝对路径。

`ToolExecutor` 当前不是通用插件平台，不动态注册任意工具，不实现权限系统、人工审批或沙箱执行。

## 后续工具执行边界

未来高风险工具调用应继续沿用当前 Kernel 链路，在进入实际 executor 前经过权限和审批边界：

```text
ChatService
  -> CodeAgent
  -> AgentLoop
  -> ToolRegistry
  -> PermissionPolicy
  -> ApprovalGate
  -> ToolExecutor
  -> SandboxRunner（仅未来命令类工具）
  -> 具体工具
```

这样权限管理、人工审批、工具调用审计和沙箱执行都可以增量加入，不需要推倒当前 API、Service、Agent 分层。V7 当前只实现确定性 `PermissionPolicy` 和最小 `ApprovalGate`，真实审批流程和 `SandboxRunner` 仍留到后续阶段。

`PermissionPolicy` 和最小 `ApprovalGate` 已在 V7 中作为确定性运行时边界实现；`ApprovalGate` 当前不做真实交互审批或持久化。`SandboxRunner` 仍是 Roadmap，不是当前已实现能力。

## 架构约束

- `main.py` 只创建应用和注册 router。
- API 层不直接读文件、不执行工具、不写业务逻辑。
- Service 层负责编排，不直接实现仓库搜索细节。
- Agent 层负责决策和组织工具调用。
- Tools 层只提供可调用能力，不处理 HTTP。
- `ToolExecutor` 负责统一执行入口和工具调用摘要，不承载复杂业务推理。
- `PermissionPolicy` 负责在工具调用前产出 `allow`、`deny` 或 `ask` 决策。
- `ApprovalGate` 当前只消费权限决策并阻止 `ask` 分支执行工具，不实现真实审批 UI。
- 高风险能力以后必须经过 `ToolExecutor`，不能散落在各模块里。

## 暂不引入

- 真实 LLM。
- LangGraph。
- RAG。
- Memory。
- 多 Agent。
- 自动修改代码。
- 沙箱执行命令。
- SandboxRunner 的实际实现。
- 真实审批 UI 或审批持久化。
- trace 持久化审计。
