## 1. Harness

- [x] 1.1 对齐旧 `v6-skill-aware-agent-loop` draft 与当前 V6 Kernel 草稿的去留状态。
  - 已按用户确认保留并改造当前 V6 Kernel 草稿；旧 Provider/Context/Skill/SessionStore 运行时代码已从 V6 Kernel 草稿移除。
- [x] 1.2 创建 `v6-agent-harness-kernel` OpenSpec change。
- [x] 1.3 更新 `.harness/allowed_files.md`。
- [x] 1.4 更新 `.harness/review_checklist.md`。

## 2. OpenSpec

- [x] 2.1 编写 V6 Agent Harness Kernel proposal。
- [x] 2.2 编写 V6 Agent Harness Kernel design。
- [x] 2.3 编写 `agent-loop-tool-execution` spec delta。
- [x] 2.4 编写 `harness-development-workflow` spec delta。
- [x] 2.5 运行 `openspec validate v6-agent-harness-kernel`。

## 3. Tests

- [x] 3.1 为 `AgentLoopRequest(message, repo_path, trace_id)` 和 `RouteDecision(route, keyword, reason)` 增加失败测试，覆盖 `repo_search` 和 `chat_only`。
- [x] 3.2 为 `ToolSpec(name, description, read_only, risk)` 增加失败测试，覆盖默认 `search_code` 为只读且 `low` 风险；`ToolRegistry` 仅登记元数据和提供校验，不负责 dispatch。
- [x] 3.3 为 `AgentLoop` 工具调用前 registry 校验增加失败测试，覆盖未注册、非只读或高风险工具不得调用 `ToolExecutor.search_code`，并记录稳定拒绝原因。
- [x] 3.4 为 `TraceEvent(event_type, tool_name, status, summary)` 增加失败测试，覆盖路由、工具调用、工具结果和拒绝事件。
- [x] 3.5 为 `/chat` 通过 Kernel 保持现有搜索行为增加回归测试。

## 4. Implementation

- [x] 4.1 新增 `app/harness/__init__.py`。
- [x] 4.2 新增 `app/harness/kernel.py`，实现 `AgentLoopRequest`、`RouteDecision`、`ToolSpec`、`TraceEvent`、`AgentLoopResult`、`RequestRouter`、`ToolRegistry` 和 `AgentLoop` 的最小骨架；`ToolRegistry` 只做元数据登记和调用前校验，不做工具 dispatch。
- [x] 4.3 让 `AgentLoop` 调用工具前通过 `ToolRegistry` 校验工具存在、只读和风险等级。
- [x] 4.4 让 `CodeAgent` 通过 Kernel 执行现有确定性搜索闭环。
- [x] 4.5 保持 `/chat` API schema 和安全摘要不变。

## 5. Docs and Verification

- [x] 5.1 更新 `README.md`。
- [x] 5.2 更新 `docs/PROGRESS.md`。
- [x] 5.3 更新 `docs/FEATURE_LIST.json`。
- [x] 5.4 更新 `HANDOFF_TO_NEXT_CHAT.md`。
- [x] 5.5 运行 `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`。
- [x] 5.6 运行 `git diff --check`。
