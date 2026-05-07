# RepoPilot

RepoPilot 是一个面向代码仓库分析任务的可控 Code Agent Harness，目标不是替代通用 AI IDE 或 AI 编程助手，而是围绕 Agent 的工具调用、安全边界、执行追踪、评测和交接机制，构建一个可验证、可审计、可扩展的代码智能体执行框架。当前应用场景包括代码仓库阅读、Bug 定位和修复建议。

当前实现包含 V1 Agent 服务入口、V2 安全只读仓库工具层和 V3 最小确定性 Agent Loop。项目价值不在于“更会写代码”，而在于让 Agent 执行过程有明确边界、可观察输出和可交接规则。

## 当前能力与定位

- 提供 FastAPI 应用和 `POST /chat`，作为 Agent 服务入口。
- 请求字段包含 `user_id`、`session_id`、`message` 和 `repo_path`。
- 每次请求生成唯一 `trace_id`，响应保留 `related_files` 和 `tool_calls` 审计字段。
- `CodeAgent` 当前使用最小确定性关键词提取，不接真实 LLM。
- `ToolExecutor` 统一收口只读工具调用，当前包装 `search_code`。
- `related_files` 和 `tool_calls` 返回真实只读搜索结果。
- 使用 specs、harness rules、review checklist、pytest 和 handoff 约束开发过程。
- 提供安全只读仓库文件工具：
  - `list_files(repo_path)`
  - `read_file(repo_path, file_path, max_chars=12000)`
  - `search_code(repo_path, keyword, max_results=20)`

V3 当前只做确定性关键词搜索，不做复杂语义理解。

## 阶段说明

### V1：Agent 服务入口和可追踪请求结构

V1 的意义不是普通 mock 接口，而是建立可测试的 Agent 服务入口：

- `POST /chat`
- `ChatRequest` / `ChatResponse`
- `trace_id`
- `related_files` / `tool_calls` 响应字段
- pytest 接口测试

### V2：安全只读仓库工具层

V2 的意义不是普通文件读取，而是建立仓库访问安全边界：

- `list_files`
- `read_file`
- `search_code`
- `repo_path` 内部访问限制和路径逃逸防护
- 敏感文件、隐藏目录、忽略目录和二进制文件过滤
- 只读工具单元测试

### V3：统一工具执行边界

V3 的意义不是让 Agent 变聪明，而是把工具调用收口到 `ToolExecutor`：

- `CodeAgent` 通过 `ToolExecutor` 调用 `search_code`
- `/chat` 返回真实 `related_files`
- `/chat` 返回 `tool_calls` 摘要
- `tool_calls` 不包含完整文件内容、完整搜索结果或本机绝对路径
- 为后续 `PermissionPolicy`、`ApprovalGate`、`SandboxRunner`、trace audit、eval 和 reflection 留出扩展点

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
    "message": "帮我分析 UNIQUE_BUG_TOKEN",
    "repo_path": "./mock_repo"
  }'
```

响应示例：

```json
{
  "trace_id": "trace_xxx",
  "answer": "已使用只读仓库工具搜索 `UNIQUE_BUG_TOKEN`，找到相关文件。",
  "related_files": ["app/example.py"],
  "tool_calls": [
    {
      "tool_name": "search_code",
      "keyword": "UNIQUE_BUG_TOKEN",
      "status": "success",
      "result_count": "1"
    }
  ]
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

## 当前架构

```text
API -> ChatService(trace_id) -> CodeAgent -> ToolExecutor -> file_tools
```

- `app/main.py`：创建 FastAPI 应用并注册路由。
- `app/api/chat.py`：暴露聊天接口。
- `app/schemas/chat.py`：定义请求和响应模型。
- `app/services/chat_service.py`：创建请求级 `trace_id` 并编排智能体调用。
- `app/agents/code_agent.py`：提取关键词、调用工具并组织结果。
- `app/tools/tool_executor.py`：统一包装只读工具调用。
- `app/tools/file_tools.py`：提供安全仓库文件工具。
- `app/observability/tracing.py`：生成请求级 `trace_id`；当前不是完整持久化审计系统。

## 当前流程暂不包含

- 真实 LLM 接入。
- 技能加载器。
- PermissionPolicy、ApprovalGate 或 SandboxRunner 实现。
- trace 持久化审计。
- 反思检查。
- 评测。
- RAG。
- Memory。
- 自动修改代码。
- shell 执行。
- 复杂智能体循环和复杂语义理解。

## 文件工具安全边界

V2 文件工具是只读工具，不执行 shell 命令。它们会把访问限制在 `repo_path` 内，拒绝路径穿越，跳过忽略目录，过滤 `.env` 和私钥等敏感文件，忽略二进制文件，并限制读取和搜索返回规模。

## 后续安全架构

V2 提供的是工具级安全边界，不是完整的权限系统、沙箱系统或人工审批流。这是有意为之，因为当前工具只读；V3 已经通过 `ToolExecutor` 把 `search_code` 接入 `/chat`，后续高风险能力仍必须继续经过统一执行层扩展。

未来高风险能力应统一放到 `ToolExecutor` 层之后：

```text
ChatService
  -> CodeAgent
  -> ToolExecutor
  -> PermissionPolicy / ApprovalGate / SandboxRunner
  -> 具体工具
```

这样可以把后续安全能力做成增量扩展，而不是重写现有代码。权限检查、人工介入审批、工具调用审计和沙箱命令执行都应该围绕 `ToolExecutor` 实现，不应该散落在 `main.py`、API handler 或具体工具函数里。

已实现和建议演进：

- V3 已实现：让 `CodeAgent` 通过轻量 `ToolExecutor` 调用只读 `search_code`。
- 后续：为每次工具调用增加 trace 和审计记录。
- 后续：增加 `PermissionPolicy`，支持用户、仓库和工具级允许规则。
- 后续：在写文件、运行命令、提交代码或创建 PR 等高风险动作前增加 `ApprovalGate`。
- 后续：仅为执行命令类工具增加 `SandboxRunner`，例如测试运行器。

## 路线图

- V2：加入安全仓库工具：`list_files`、`read_file` 和 `search_code`。
- V3：加入简单规则型智能体循环和统一 `ToolExecutor`。
- V4：加入基于 markdown 的技能加载器。
- V5：扩展 trace，记录工具调用和检索文件。
- V6：加入仓库调试小型评测。
- V7：加入回答完整性反思检查。
- V8：探索面向大型仓库的 RAG。
