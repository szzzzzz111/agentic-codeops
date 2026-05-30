## Why

V13 已经完成 repo-local SQLite-backed Memory，但当前 `/chat` 仍主要是单请求闭环：一次请求完成后，系统没有可恢复的任务状态、计划步骤、scratch 摘要或可审计的 ReAct step 记录。继续只做单轮 repo_search 会限制后续 always-on、subagents、worktree handoff 和人工审批流程的演进。

V14 需要实现一个轻量但真实可用的 Long Task Control Plane：通过明确聊天指令创建、查看、列出、暂停、恢复、补充和归档任务；用 repo-local SQLite 保存任务状态；每次显式推进只执行一个只读 `repo_rag` step，并记录摘要级 ReAct trace。该能力必须保持 `/chat` 顶层 contract 不变，并继续保护 ToolExecutor、PermissionPolicy、ApprovalGate、Evidence Pack、Model Provider 和 Memory 边界。

## What Changes

- 新增 `app/longtask` 模块，提供 long task 类型、repo-local SQLite store、自然语言命令 parser、任务类型模板 planner 和 manager。
- 新增 `.repopilot/tasks.sqlite3` 作为 long task 本地状态存储，不复用 V13 `memory.sqlite3`。
- Long Task 指令解析前置于 `RequestRouter` / keyword 路由，并与 V13 memory command 同级处理，避免 `task_xxx` 误触发 repo_search。
- 创建任务只保存 plan，不自动执行；显式 resume/run 每次只推进一个 step。
- step action 只允许现有只读 `repo_rag`，且必须经过 ToolRegistry、PermissionPolicy、ApprovalGate 和 ToolExecutor。
- 保存摘要级 ReAct trace 和 scratch 摘要，不公开完整 scratch、完整 Evidence Pack、完整 provider prompt/output、本机绝对路径或 DB 路径。
- 默认使用 deterministic task-type templates；真实 ModelProvider planning 仅作为显式配置后的增强，失败时 fallback 到 deterministic plan。
- 预留 subagent/worktree handoff metadata，但不创建、展示、调度真实 subagents，也不执行 git branch/worktree 操作。

## Capabilities

### New Capabilities

- `long-task-agent-execution`: 记录 Long Task 的命令解析、状态机、SQLite 存储、任务类型模板、ReAct trace skeleton、scratch、quota/archive、provider planning fallback 和审计边界。

### Modified Capabilities

- `agent-loop-tool-execution`: AgentLoop 前置处理 Long Task 指令，并在 resume/run 时通过现有权限、审批和 ToolExecutor 边界执行只读 `repo_rag` step。
- `chat-api`: `/chat` 响应 contract 保持不变；Long Task 确认、状态和步骤摘要写入现有 `answer` 字段。
- `harness-development-workflow`: V14 阶段 harness 边界和 review checklist 固化 Long Task 的非目标和验证规则。

## Impact

- Code: `app/longtask/**`, `app/harness/kernel.py`
- Tests: `tests/test_long_task.py`, `tests/test_agent_harness_kernel.py`, `tests/test_chat_api.py`
- Docs: `README.md`, `docs/ARCHITECTURE.md`, `docs/PROGRESS.md`, `docs/FEATURE_LIST.json`, `HANDOFF_TO_NEXT_CHAT.md`
- OpenSpec / Harness: `openspec/changes/v14-long-task-react-subagents/**`, `openspec/specs/**`, `.harness/allowed_files.md`, `.harness/review_checklist.md`
- Dependencies: none.
