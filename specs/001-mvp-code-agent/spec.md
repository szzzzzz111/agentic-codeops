# 规格：V1 MVP 代码智能体

## 项目目标

RepoPilot 是一个智能化 CodeOps 项目，面向代码仓库阅读、Bug 分析和修复建议。V1 的范围是做出一个可以运行的 FastAPI 骨架，并为后续仓库工具、技能、trace、评测和反思检查保留清晰扩展点。

## V1 目标

构建最小可用 API 闭环：

- FastAPI 应用可以成功启动。
- `POST /chat` 接收 `user_id`、`session_id`、`message` 和 `repo_path`。
- Service 返回模拟代码分析结果。
- 每次请求生成一个 `trace_id`。
- 响应包含 `trace_id`、`answer`、`related_files` 和 `tool_calls`。
- pytest 覆盖 `/chat` 接口。
- 连续两次请求返回不同的 `trace_id`。

## 请求契约

`POST /chat`

```json
{
  "user_id": "u001",
  "session_id": "s001",
  "message": "帮我分析为什么测试失败",
  "repo_path": "./mock_repo"
}
```

## 响应契约

```json
{
  "trace_id": "trace_xxx",
  "answer": "模拟分析结果：V1 还不会读取 ./mock_repo。V2 会加入 list_files/read_file/search_code 工具。",
  "related_files": [],
  "tool_calls": []
}
```

## 架构边界

V1 流程：

```text
API -> ChatService -> CodeAgent -> Trace
```

职责：

- API 层只接收 HTTP 请求并返回 schema 对象。
- Service 层创建 `trace_id` 并编排智能体调用。
- Agent 层返回模拟分析结果。
- Trace 层生成 trace 标识符。

## 明确不做

V1 不做：

- 接入真实 LLM。
- 读取 `repo_path` 中的文件。
- 实现 `list_files`、`read_file` 或 `search_code`。
- 实现技能加载器。
- 实现反思检查。
- 实现评测。
- 实现复杂智能体循环。
- 自动修改仓库代码。
- 把所有逻辑都写进 `main.py`。

## 验收标准

- `uvicorn app.main:app --reload` 可以启动 API。
- `POST /chat` 接收 V1 请求字段。
- 响应包含 `trace_id`、`answer`、`related_files` 和 `tool_calls`。
- V1 中 `related_files` 和 `tool_calls` 为空列表。
- 连续两次请求返回不同的 `trace_id`。
- 模拟回答说明 V1 不读取 `repo_path`，并说明 V2 会加入仓库工具。
- `pytest` 通过。
- `ruff` 作为质量闸门可用。
- README 说明当前能力和路线图。
