# 规格：V3 Agent Loop

## 目标

V3 引入最小确定性 Agent Loop，让 `CodeAgent` 可以通过轻量 `ToolExecutor` 调用 V2 已有的只读文件工具。V3 的核心目标不是接入真实 LLM，而是让 `/chat` 从模拟占位响应前进到可验证的仓库搜索响应。

## 请求契约

`POST /chat` 请求字段保持不变：

```json
{
  "user_id": "u001",
  "session_id": "s001",
  "message": "帮我分析 UNIQUE_BUG_TOKEN",
  "repo_path": "./mock_repo"
}
```

## 响应契约

响应字段保持不变：

```json
{
  "trace_id": "trace_xxx",
  "answer": "基于只读仓库工具的分析结果。",
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

V3 只填充已有的 `related_files` 和 `tool_calls` 字段，不新增 API 字段。

## Agent 行为

- `CodeAgent` 使用确定性规则从 `message` 中提取一个搜索关键词。
- 如果 `message` 中包含明确 token，例如函数名、类名、文件名、错误关键字或测试用唯一关键词，则优先取其中一个作为 `search_code` 的 `keyword`。
- 测试用例必须使用唯一关键词，例如 `UNIQUE_BUG_TOKEN`，避免依赖复杂自然语言理解。
- 如果无法提取明确关键词，可以使用 `message` 原文作为关键词，或返回无命中结果。
- V3 不做复杂语义理解、不推断用户真实意图、不引入 LLM。

## 工具调用

- 工具调用必须经过 `ToolExecutor`。
- V3 最小实现优先只调用 `search_code(repo_path, keyword)`。
- `related_files` 来自 `search_code` 命中的 `file_path`，去重后返回。
- `tool_calls` 记录工具名称、参数摘要、状态和结果数量，不记录完整文件内容。
- 工具无命中时，`related_files` 返回空列表，API 仍保持稳定响应。

## 安全要求

- 不写文件。
- 不删除文件。
- 不执行 shell 命令。
- 不接真实 LLM。
- 不自动修改代码。
- 不加入多 Agent、RAG、Memory、Reflection 或 eval。
- 继续复用 V2 文件工具的仓库边界、敏感文件过滤和结果数量限制。

## 验收标准

- `POST /chat` 使用包含 `UNIQUE_BUG_TOKEN` 的 `message` 和临时仓库时，能够通过 `search_code` 命中文件。
- 响应中的 `related_files` 包含命中文件路径。
- 响应中的 `tool_calls` 包含 `search_code`、关键词摘要、状态和结果数量。
- 无命中时返回空 `related_files`，API 状态仍为 200。
- 不泄露敏感文件内容。
- 既有 V1/V2 测试继续通过。
- `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1` 通过；如果当前环境没有 ruff，应明确说明已跳过。

## 非目标

- 真实 LLM 接入。
- 代码修改、补丁生成或自动修复。
- shell 工具或测试运行工具。
- 权限系统、人工审批流或沙箱执行。
- 技能加载器。
- RAG、Memory、Reflection 或 eval。
