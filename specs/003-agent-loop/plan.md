# 计划：V3 Agent Loop

## 文件

V3 实际修改：

- `specs/003-agent-loop/spec.md`：V3 范围、行为和验收标准。
- `specs/003-agent-loop/plan.md`：V3 实现计划和完成记录。
- `specs/003-agent-loop/tasks.md`：V3 任务清单。
- `app/agents/code_agent.py`：最小确定性关键词提取和工具调用组织。
- `app/tools/tool_executor.py`：统一包装只读 `search_code` 调用。
- `tests/test_chat_api.py`：覆盖命中、无命中、敏感文件不泄露和错误摘要脱敏。
- `.harness/allowed_files.md`：V3 实现阶段允许文件。
- `.harness/review_checklist.md`：V3 实现阶段评审清单。
- `README.md`、`docs/PROGRESS.md`、`HANDOFF_TO_NEXT_CHAT.md`、`docs/FEATURE_LIST.json`：记录 V3 完成状态。

V3 未开放写文件工具、shell 工具、真实 LLM、多 Agent、RAG、Memory、Reflection 或 eval。

## 实现设计

V3 实现链路：

```text
ChatService -> CodeAgent -> ToolExecutor -> file_tools.search_code
```

- `ChatService` 继续负责生成 `trace_id` 和编排 `CodeAgent`。
- `CodeAgent` 负责确定关键词、调用 `ToolExecutor`、组织回答和返回 `AgentResult`。
- `ToolExecutor` 负责统一包装只读工具调用，V3 最小实现只支持 `search_code`。
- `file_tools` 继续负责仓库安全边界，不处理 HTTP 或 Agent 决策。

## 关键词提取

V3 使用最小确定性规则：

- 优先提取 `message` 中明显可搜索的 token。
- 明显 token 包括函数名、类名、文件名、错误关键字和测试用唯一关键词。
- 测试用例使用 `UNIQUE_BUG_TOKEN`，确保搜索行为稳定可验收。
- 如果没有可识别 token，可以直接使用 `message` 原文作为搜索词，或返回无命中结果。
- 不做复杂语义理解，不调用模型辅助提取。

## 工具调用记录

`tool_calls` 只记录参数摘要：

```json
{
  "tool_name": "search_code",
  "keyword": "UNIQUE_BUG_TOKEN",
  "status": "success",
  "result_count": "1"
}
```

不在 `tool_calls` 中记录完整文件内容、完整搜索结果、敏感信息或本机绝对路径。

## 返回结果

- `related_files` 从 `search_code` 结果中的 `file_path` 提取。
- 多个命中文件去重后返回，保持稳定顺序。
- 无命中时返回空列表。
- `answer` 可以说明是否找到相关文件，但不伪造分析结论。

## 开发顺序和完成状态

1. 已切换到 `feature/v3-agent-loop`。
2. 已写 V3 specs、plan、tasks。
3. 已更新 harness 允许文件和评审清单。
4. 已开放 V3 实现需要的运行时代码和测试文件。
5. 已实现轻量 `ToolExecutor`。
6. 已让 `CodeAgent` 调用 `ToolExecutor.search_code`。
7. 已增加 `/chat` 集成测试。
8. 已更新 README、PROGRESS、HANDOFF 和 FEATURE_LIST。
9. 已运行 `scripts/verify.ps1`，`pytest` 和 `ruff check .` 通过。

## 测试策略

V3 使用临时仓库构造确定性案例：

- 普通文件包含 `UNIQUE_BUG_TOKEN`，请求 message 也包含该 token。
- 敏感文件也包含同一 token，确认不会泄露。
- 无匹配 token 时确认 API 稳定返回 200 和空结果。
- 缺失 repo 路径时确认错误摘要不泄露本机绝对路径。
- 既有 V1/V2 测试继续通过。
