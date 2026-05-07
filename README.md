# RepoPilot

RepoPilot 是一个智能化 CodeOps 项目，目标是面向代码仓库阅读、Bug 分析和修复建议构建一个渐进式代码智能体。当前实现包含 V1 FastAPI 聊天接口和 V2 安全仓库文件工具。`/chat` 目前仍使用模拟 `CodeAgent`；V2 文件工具还没有接入智能体循环。

## 当前能力

- 提供 FastAPI 应用和 `POST /chat` 接口。
- 请求字段包含 `user_id`、`session_id`、`message` 和 `repo_path`。
- `CodeAgent` 当前返回模拟分析结果。
- 每次请求生成唯一 `trace_id`。
- `related_files` 和 `tool_calls` 作为后续工具接入的占位字段。
- 使用 pytest 覆盖聊天接口。
- 提供安全仓库文件工具：
  - `list_files(repo_path)`
  - `read_file(repo_path, file_path, max_chars=12000)`
  - `search_code(repo_path, keyword, max_results=20)`

V2 文件工具目前还没有连接到 `/chat`，该集成计划放到 V3。

## Harness Engineering

本仓库包含一套轻量 Harness V0，用来让 Agent 开发过程可控、可验证、可交接：

- `AGENTS.md`：Agent 入口地图。
- `docs/ARCHITECTURE.md`：架构边界。
- `docs/AGENT_RULES.md`：Agent 工作规则。
- `docs/PROGRESS.md`：项目长期进度记忆。
- `docs/FEATURE_LIST.json`：可验收功能清单。
- `HANDOFF_TO_NEXT_CHAT.md`：跨 session 交接文档。
- `scripts/verify.ps1`：本地验证入口。

## 启动接口

```bash
uvicorn app.main:app --reload
```

接口地址：

```text
http://127.0.0.1:8000
```

## 请求示例

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "u001",
    "session_id": "s001",
    "message": "帮我分析为什么测试失败",
    "repo_path": "./mock_repo"
  }'
```

响应示例：

```json
{
  "trace_id": "trace_xxx",
  "answer": "模拟分析结果：V1 已收到请求，但不会读取 ./mock_repo。V2 会加入 list_files/read_file/search_code 工具，用于安全的仓库分析。",
  "related_files": [],
  "tool_calls": []
}
```

## 运行测试

```bash
pytest
```

可选静态检查：

```bash
ruff check .
```

## V1 架构

```text
API -> ChatService -> CodeAgent -> Trace
```

- `app/main.py`：创建 FastAPI 应用并注册路由。
- `app/api/chat.py`：暴露聊天接口。
- `app/schemas/chat.py`：定义请求和响应模型。
- `app/services/chat_service.py`：编排 trace 创建和智能体调用。
- `app/agents/code_agent.py`：返回模拟分析结果。
- `app/observability/tracing.py`：生成 trace ID。

## 当前流程暂不包含

- 真实 LLM 接入。
- `/chat` 读取真实仓库。
- 技能加载器。
- 反思检查。
- 评测。
- 自动修改代码。
- 复杂智能体循环。

## 文件工具安全边界

V2 文件工具是只读工具，不执行 shell 命令。它们会把访问限制在 `repo_path` 内，拒绝路径穿越，跳过忽略目录，过滤 `.env` 和私钥等敏感文件，忽略二进制文件，并限制读取和搜索返回规模。

## 后续安全架构

V2 提供的是工具级安全边界，不是完整的权限系统、沙箱系统或人工审批流。这是有意为之，因为当前工具只读，且还没有连接到智能体循环。

未来高风险能力应统一放到 `ToolExecutor` 层之后：

```text
ChatService
  -> CodeAgent
  -> ToolExecutor
  -> PermissionPolicy / ApprovalGate / SandboxRunner
  -> 具体工具
```

这样可以把后续安全能力做成增量扩展，而不是重写现有代码。权限检查、人工介入审批、工具调用审计和沙箱命令执行都应该围绕 `ToolExecutor` 实现，不应该散落在 `main.py`、API handler 或具体工具函数里。

建议演进：

- V3：让 `CodeAgent` 通过轻量 `ToolExecutor` 调用只读文件工具。
- 后续：为每次工具调用增加 trace 和审计记录。
- 后续：增加 `PermissionPolicy`，支持用户、仓库和工具级允许规则。
- 后续：在写文件、运行命令、提交代码或创建 PR 等高风险动作前增加 `ApprovalGate`。
- 后续：仅为执行命令类工具增加 `SandboxRunner`，例如测试运行器。

## 路线图

- V2：加入安全仓库工具：`list_files`、`read_file` 和 `search_code`。
- V3：加入简单规则型智能体循环。
- V4：加入基于 markdown 的技能加载器。
- V5：扩展 trace，记录工具调用和检索文件。
- V6：加入仓库调试小型评测。
- V7：加入回答完整性反思检查。
- V8：探索面向大型仓库的 RAG。
