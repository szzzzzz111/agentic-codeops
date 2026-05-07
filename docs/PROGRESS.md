# 项目进度

## 当前状态

- 当前功能分支：`feature/v2-file-tools`
- 当前阶段：V2 安全仓库文件工具层
- 当前主流程：`/chat` 仍使用模拟 `CodeAgent`
- 当前工具层：`list_files`、`read_file`、`search_code` 已实现

## 已完成

### V1：FastAPI 聊天接口

- FastAPI 应用可启动。
- `POST /chat` 接收 `user_id`、`session_id`、`message`、`repo_path`。
- 每次请求生成唯一 `trace_id`。
- 返回 `answer`、`related_files`、`tool_calls`。
- V1 不读取真实仓库。
- pytest 覆盖 `/chat` 基础行为和 `trace_id` 不重复。

### V2：安全只读文件工具

- `list_files(repo_path)`：列出仓库内允许访问的文本文件。
- `read_file(repo_path, file_path, max_chars=12000)`：读取仓库内文本文件并限制长度。
- `search_code(repo_path, keyword, max_results=20)`：搜索关键词并限制结果数。
- 文件工具限制访问在 `repo_path` 内。
- 跳过敏感文件、隐藏目录、忽略目录和二进制文件。
- 新增 `tests/test_file_tools.py`。

### Harness V0

- 新增 `AGENTS.md` 作为 Agent 入口地图。
- 新增 `docs/ARCHITECTURE.md` 记录架构边界。
- 新增 `docs/AGENT_RULES.md` 记录 Agent 工作规则。
- 新增 `docs/FEATURE_LIST.json` 记录可验收功能清单。
- 新增 `HANDOFF_TO_NEXT_CHAT.md` 作为跨 session 交接文档。
- 新增 `scripts/verify.ps1` 作为本地验证入口。

## 最近验证

- `pytest`：13 passed
- `ruff check .`：当前环境未安装 ruff 时会在 `scripts/verify.ps1` 中提示跳过

## 当前注意事项

- `/chat` 还没有接入 V2 文件工具。
- V2 工具只读，不写文件、不删文件、不执行 shell。
- 后续接入权限、审批、沙箱时，应通过 `ToolExecutor` 增量加入。
- 缓存文件已从 git 跟踪中移除，并由 `.gitignore` 忽略。

## 下一步建议

V3 开始前创建或切换到：

```text
feature/v3-agent-loop
```

V3 目标：

- 引入轻量 `ToolExecutor`。
- 让 `CodeAgent` 通过 `ToolExecutor` 调用只读文件工具。
- `/chat` 返回真实 `related_files` 和 `tool_calls`。
- 保持不接真实 LLM、不自动修改代码。
