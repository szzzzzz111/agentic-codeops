## Why

V14 已经把 Memory、Long Task、repo-local hybrid RAG 和 grounded answer 边界接入 `/chat`，但用户仍需要记住多套指令：普通代码问题走 RAG，`记住`/`忘记` 管理 Memory，`创建长任务`/`恢复任务` 管理 Long Task，能力状态问题走 capability-status。当前缺少一个轻量、只读、可审计的助手控制入口，用来说明 RepoPilot 当前能做什么、本地状态如何、下一步应该使用哪些命令。

V15 需要把这些既有能力组织成 Assistant Control Surface：仍只使用 `/chat` 和现有 `answer` 字段，不新增 API 或响应字段；状态聚合只读，不触发 repo_rag、不写 memory、不创建任务，也不隐式初始化 `.repopilot` DB。

## What Changes

- 新增 `assistant-control-surface` capability，定义明确状态类聊天指令、只读状态聚合和公开回答边界。
- 新增 Assistant Control Surface 运行时模块，用于识别 `助手状态`、`RepoPilot 状态`、`你能做什么`、`assistant status`、`what can you do` 等明确控制面请求。
- AgentLoop 在 Memory command 和 Long Task command 之后、capability-status 和 repo_search 之前处理 Assistant Control Surface 请求。
- 控制面回答通过现有 `/chat.answer` 返回能力摘要、Memory/Long Task 只读状态摘要和下一步命令建议。
- Memory 和 Long Task 提供只读 summary 入口；不存在 `.repopilot` DB 时返回空状态或 unavailable 摘要，不创建目录或数据库。
- `/chat` 顶层响应 contract 保持不变，`tool_calls` 在控制面状态请求中保持空列表。

## Capabilities

### New Capabilities

- `assistant-control-surface`: 记录 `/chat` 内的只读助手控制面、触发词、状态聚合、脱敏边界和非目标。

### Modified Capabilities

- `agent-loop-tool-execution`: AgentLoop 增加 Assistant Control Surface 前置分支，并保持 Memory/Long Task 优先级。
- `chat-api`: `/chat` 响应 contract 不变；控制面状态进入现有 `answer`。
- `memory`: 增加只读状态摘要要求，不泄露 memory value，不隐式创建 DB。
- `long-task-agent-execution`: 增加只读任务状态摘要要求，不泄露 scratch/ReAct trace，不隐式创建 DB。
- `harness-development-workflow`: 固化 V15 的 OpenSpec、harness、review 和 non-goal 边界。

## Impact

- Code: `app/assistant/**`, `app/harness/kernel.py`, `app/memory/manager.py`, `app/longtask/manager.py`
- Tests: `tests/test_assistant_control_surface.py`, `tests/test_agent_harness_kernel.py`, `tests/test_chat_api.py`
- Docs: `README.md`, `docs/ARCHITECTURE.md`, `docs/PROGRESS.md`, `docs/FEATURE_LIST.json`, `HANDOFF_TO_NEXT_CHAT.md`
- OpenSpec / Harness: `openspec/changes/v15-assistant-control-surface/**`, `openspec/specs/**`, `.harness/allowed_files.md`, `.harness/review_checklist.md`
- Dependencies: none.
