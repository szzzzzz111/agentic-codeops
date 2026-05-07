# 架构说明

RepoPilot 当前采用渐进式架构。目标不是一开始做复杂多 Agent 系统，而是先让主流程可运行、可测试、可解释，再逐步接入工具、技能、评测和安全治理。

## 当前主链路

```text
API -> ChatService -> CodeAgent -> Trace
```

- API 层只接收请求并返回响应。
- `ChatService` 负责编排请求、生成 `trace_id`、调用智能体。
- `CodeAgent` 当前仍返回模拟分析结果。
- Trace 层当前只负责生成唯一 `trace_id`。

## V2 工具层

V2 新增安全只读文件工具：

```text
app/tools/file_tools.py
```

包含：

- `list_files(repo_path)`
- `read_file(repo_path, file_path, max_chars=12000)`
- `search_code(repo_path, keyword, max_results=20)`

这些工具当前没有接入 `/chat`，只作为 V3 Agent Loop 的基础。

## 后续工具执行边界

未来工具调用应集中经过 `ToolExecutor`：

```text
ChatService
  -> CodeAgent
  -> ToolExecutor
  -> PermissionPolicy / ApprovalGate / SandboxRunner
  -> 具体工具
```

这样权限管理、人工审批、工具调用审计和沙箱执行都可以增量加入，不需要推倒当前 API、Service、Agent 分层。

## 架构约束

- `main.py` 只创建应用和注册 router。
- API 层不直接读文件、不执行工具、不写业务逻辑。
- Service 层负责编排，不直接实现仓库搜索细节。
- Agent 层负责决策和组织工具调用。
- Tools 层只提供可调用能力，不处理 HTTP。
- 高风险能力以后必须经过 `ToolExecutor`，不能散落在各模块里。

## 暂不引入

- 真实 LLM。
- LangGraph。
- RAG。
- Memory。
- 多 Agent。
- 自动修改代码。
- 沙箱执行命令。
