# 任务：V1 MVP 代码智能体

## 实现

- [x] 创建项目目录结构。
- [x] 编写 V1 spec、plan 和 task 文档。
- [x] 编写轻量 harness 规则。
- [ ] 实现 FastAPI 应用创建。
- [ ] 在 `app/` 下增加包标记 `__init__.py` 文件。
- [ ] 实现 `/chat` router。
- [ ] 实现 chat 请求和响应 schema。
- [ ] 实现 trace ID 生成。
- [ ] 实现模拟代码智能体，并在回答中说明 V1 不读取 `repo_path`。
- [ ] 实现聊天 service 编排。
- [ ] 增加 `/chat` pytest 覆盖，包括连续请求 `trace_id` 不重复。
- [ ] 编写 README，包含启动、测试、当前范围和路线图。
- [ ] 在 `pyproject.toml` 中加入 `ruff` 质量闸门。

## 验证

- [ ] 运行 `pytest`。
- [ ] 运行 `ruff check .`。
- [ ] 确认 `uvicorn app.main:app --reload` 是文档中的启动命令。

## 延后

- [ ] 加入仓库文件工具。
- [ ] 加入基础智能体循环。
- [ ] 加入技能加载器。
- [ ] 加入 trace 持久化。
- [ ] 加入小型评测。
- [ ] 加入反思检查。
