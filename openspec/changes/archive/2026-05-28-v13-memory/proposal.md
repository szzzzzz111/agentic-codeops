## Why

V12 已经完成 deterministic query rewrite/rerank，当前 `/chat` 仍是单请求闭环：系统不会稳定记住用户偏好、会话短期信息或用户明确要求保留的项目事实。继续只保留接口会让路线停留在边界设计，缺少真实可用的纵向能力。

V13 需要实现一个轻量但真实可用的 Memory 切片：默认使用 repo-local SQLite 存储 PREF/LTM，使用进程内 STM，并通过明确聊天指令完成读写和删除。Memory 必须可审计、可测试、可禁用失败影响，且不得改变 `/chat` 顶层响应 contract。

## What Changes

- 新增 Memory 模块，提供 `SQLiteMemoryStore`、`InMemorySessionMemoryStore` 和 `MemoryManager`。
- 使用目标 repo 内 `.repopilot/memory.sqlite3` 保存持久记忆；`.repopilot/` 必须加入 `.gitignore`。
- `repo_key` 由 `Path(repo_path).resolve()`、POSIX 分隔符、Windows lower-case 和稳定 hash 计算，不在 audit 中暴露绝对路径。
- `ChatService -> CodeAgent -> AgentLoopRequest` 传入 `user_id` 和 `session_id`，但不修改 `ChatResponse`。
- 支持明确 memory 指令：`记住: ...`、`请记住...`、`忘记: ...`、`请忘记...`、`remember: ...`、`forget: ...`；parser 先将全角冒号 `：` 归一化为半角 `:`。
- Memory 指令命中后确认优先，不执行 `repo_rag`。
- PREF 可影响回答表达偏好；代码事实仍必须由 repo evidence citation 约束。
- memory audit 只进入内部 trace，不进入 `/chat` 顶层字段或 `tool_calls`。

## Capabilities

### New Capabilities

- `memory`: 记录 STM、LTM、PREF 的存储、隔离、命令解析、删除、审计和安全边界。

### Modified Capabilities

- `agent-loop-tool-execution`: AgentLoop 接入 MemoryManager，记录 memory 内部 trace，保持 repo_search、权限、审批、ToolExecutor、Evidence Pack 和 grounded answer 边界。
- `chat-api`: `/chat` 请求字段继续包含 `user_id` 和 `session_id`，响应字段不新增必需顶层字段；memory 指令通过现有 `answer` 返回确认。

## Impact

- Code: `app/memory/**`, `app/harness/kernel.py`, `app/agents/code_agent.py`, `app/services/chat_service.py`, `.gitignore`
- Tests: `tests/test_memory.py`, `tests/test_agent_harness_kernel.py`, `tests/test_chat_api.py`
- Docs: `README.md`, `docs/ARCHITECTURE.md`, `docs/PROGRESS.md`, `docs/FEATURE_LIST.json`, `HANDOFF_TO_NEXT_CHAT.md`
- OpenSpec / Harness: `openspec/changes/v13-memory/**`, `openspec/specs/**`, `.harness/allowed_files.md`, `.harness/review_checklist.md`, `.harness/test_commands.md`
- Dependencies: none.
