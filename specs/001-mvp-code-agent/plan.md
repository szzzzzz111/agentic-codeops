# 计划：V1 MVP 代码智能体

## 新增文件

- `app/main.py`：创建 FastAPI 应用并注册路由。
- `app/__init__.py`：标记 `app` 为 Python 包。
- `app/api/chat.py`：暴露 `POST /chat` 接口。
- `app/api/__init__.py`：标记 API 目录为 Python 包。
- `app/schemas/chat.py`：定义请求和响应模型。
- `app/schemas/__init__.py`：标记 schemas 目录为 Python 包。
- `app/services/chat_service.py`：编排 trace 创建和智能体执行。
- `app/services/__init__.py`：标记 services 目录为 Python 包。
- `app/agents/code_agent.py`：返回模拟分析结果。
- `app/agents/__init__.py`：标记 agents 目录为 Python 包。
- `app/observability/tracing.py`：生成请求 trace ID。
- `app/observability/__init__.py`：标记 observability 目录为 Python 包。
- `tests/test_chat_api.py`：测试 `/chat` 接口。
- `pyproject.toml`：定义项目元数据、依赖、pytest 和 ruff 配置。
- `README.md`：说明用法和路线图。
- `.harness/*`：记录轻量编码和评审规则。

## 核心函数和类

- `create_app()`：构建 FastAPI 应用。
- `chat()`：`POST /chat` 的接口处理函数。
- `ChatRequest`：请求载荷 schema。
- `ChatResponse`：响应载荷 schema。
- `ChatService.handle_chat()`：编排一次 chat 请求。
- `CodeAgent.run()`：返回模拟智能体结果，不读取仓库。
- `generate_trace_id()`：返回唯一 trace 标识符。

## 开发顺序

1. 创建项目目录。
2. 编写 specs 和 harness 规则。
3. 定义 Pydantic schemas。
4. 实现 trace ID 生成。
5. 实现模拟 `CodeAgent`。
6. 实现 `ChatService`。
7. 在 FastAPI 中注册 `/chat` router。
8. 增加 pytest 覆盖。
9. 更新 README。
10. 运行 tests 和 ruff。

## 测试策略

- 使用 FastAPI `TestClient`。
- 断言合法 payload 调用 `/chat` 返回 HTTP 200。
- 断言响应包含符合前缀预期的 `trace_id`。
- 断言连续两次请求返回不同的 `trace_id`。
- 断言响应保留 V1 字段：`answer`、`related_files`、`tool_calls`。
- 断言 V1 不返回真实工具调用或相关文件。
- 断言模拟回答说明 V1 还不会读取 `repo_path`。

## 后续扩展点

- V2 可以在 `app/tools/` 下加入仓库工具，而不改变 API 契约。
- V3 可以把 `CodeAgent.run()` 内部替换为简单智能体循环。
- V4 可以加入 `app/skills/skill_loader.py`，同时保持 Service 边界稳定。
- V5 可以扩展 trace 数据，同时继续在响应里保留 `trace_id`。
