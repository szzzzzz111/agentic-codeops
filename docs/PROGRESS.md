# 项目进度

RepoPilot 当前定位为面向代码仓库分析任务的可控 Code Agent Harness。它不试图替代通用 AI IDE，而是围绕 Agent 工具调用边界、只读安全工具、执行追踪、可验证测试、review checklist 和 handoff 机制，构建可审计、可扩展的代码智能体执行框架。

## 当前状态

- 当前功能分支：`feature/v3-agent-loop`
- 当前阶段：V3 最小确定性 Agent Loop
- 当前主流程：`/chat` 已通过 `CodeAgent -> ToolExecutor -> search_code` 使用只读仓库搜索
- 当前工具层：`list_files`、`read_file`、`search_code` 已实现

## 已完成

### V1：Agent 服务入口和可追踪请求结构

- FastAPI 应用可启动。
- `POST /chat` 接收 `user_id`、`session_id`、`message`、`repo_path`。
- 每次请求生成唯一 `trace_id`。
- 返回 `answer`、`related_files`、`tool_calls`。
- V1 建立 Agent 服务入口和可追踪响应结构，`related_files`、`tool_calls` 作为后续审计字段保留。
- pytest 覆盖 `/chat` 基础行为和 `trace_id` 不重复。

### V2：安全只读仓库工具层

- `list_files(repo_path)`：列出仓库内允许访问的文本文件。
- `read_file(repo_path, file_path, max_chars=12000)`：读取仓库内文本文件并限制长度。
- `search_code(repo_path, keyword, max_results=20)`：搜索关键词并限制结果数。
- 文件工具限制访问在 `repo_path` 内。
- 提供路径逃逸防护，跳过敏感文件、隐藏目录、忽略目录和二进制文件。
- V2 工具只读，不写文件、不删文件、不执行 shell。
- 新增 `tests/test_file_tools.py`。

### Harness V0

- 新增 `AGENTS.md` 作为 Agent 入口地图。
- 新增 `docs/ARCHITECTURE.md` 记录架构边界。
- 新增 `docs/AGENT_RULES.md` 记录 Agent 工作规则。
- 新增 `docs/FEATURE_LIST.json` 记录可验收功能清单。
- 新增 `HANDOFF_TO_NEXT_CHAT.md` 作为跨 session 交接文档。
- 新增 `scripts/verify.ps1` 作为本地验证入口。

### V3：统一工具执行边界和最小 Agent Loop

- 新增 `specs/003-agent-loop/spec.md`，定义 V3 最小确定性 Agent Loop 范围。
- 新增 `specs/003-agent-loop/plan.md`，定义实现链路 `ChatService -> CodeAgent -> ToolExecutor -> file_tools`。
- 新增 `specs/003-agent-loop/tasks.md`，拆分计划阶段和实现阶段任务。
- 新增轻量 `ToolExecutor`，当前只包装 `search_code`。
- `CodeAgent` 使用最小确定性规则提取关键词，并通过 `ToolExecutor` 调用只读搜索。
- `/chat` 返回真实 `related_files` 和 `tool_calls` 摘要。
- V3 的意义是把工具调用统一收口，给后续权限、审批、沙箱、trace audit、eval 和 reflection 留扩展点，不是让 Agent 变成通用 AI 编程助手。
- 新增 `UNIQUE_BUG_TOKEN` 命中、无命中、敏感文件不泄露和错误摘要脱敏测试。

## 最近验证

- `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`：通过
- `pytest`：16 passed
- `ruff check .`：All checks passed

## 当前注意事项

- V2 工具只读，不写文件、不删文件、不执行 shell。
- V3 只做最小确定性关键词提取，测试使用 `UNIQUE_BUG_TOKEN`。
- V3 当前只调用 `search_code`，不自动读取完整文件内容。
- 当前不接真实 LLM、不自动修改代码、不执行 shell、不做 Reflection、eval、RAG、Memory 或复杂多 Agent。
- PermissionPolicy、ApprovalGate、SandboxRunner、trace audit、Skill Loader、eval 和 Reflection 仍是 Roadmap，不能写成已实现。
- 后续接入权限、审批、沙箱时，应通过 `ToolExecutor` 增量加入。
- 缓存文件已从 git 跟踪中移除，并由 `.gitignore` 忽略。

## 下一步建议

V4 后续建议：

- 按路线图加入基于 markdown 的技能加载器。
- 继续保持不接真实 LLM、不自动修改代码、不执行 shell。
