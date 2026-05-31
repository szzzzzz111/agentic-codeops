## Why

RepoPilot 当前能基于 repo evidence 回答代码问题，但不能把证据约束回答推进到可审查、可确认的代码改动。用户如果想让 RepoPilot 帮助修复代码，只能在聊天外手工转写建议；这缺少 patch id、确认门、写入边界和审计摘要。

V16 需要交付 Safe Patch Authoring：先基于 evidence 生成 patch proposal，再由用户明确确认 `patch_id` 后通过受控写入工具 apply。该阶段仍不运行测试、不 commit、不创建 worktree、不执行 shell，把 Verification Runner 和 Patch + Verify Loop 留给 V17/V18。

## What Changes

- 新增 `safe-patch-authoring` capability，定义 patch proposal、pending patch store、确认语法、受控 apply 和公开响应边界。
- AgentLoop 在 Assistant Control Surface 之后、capability-status / repo_search 之前处理 Patch command / Patch intent。
- 新增 Patch Authoring provider 边界：默认 fake provider 保持离线确定性且不生成真实 diff；显式 OpenAI-compatible provider 可返回结构化 JSON unified diff。
- 新增 repo-local `.repopilot/patches.sqlite3` pending patch store，按 `user_id + repo_key` 隔离。
- 新增 `ToolInvocationContext`，让 `PermissionPolicy` / `ApprovalGate` 在不扩展 `allow` / `deny` / `ask` 状态的前提下处理确认态 `patch_apply`。
- 新增受控写入工具 `patch_apply`，只允许应用已验证 unified diff 中的 repo 内相对路径。
- `/chat` 顶层响应 contract 保持不变，patch proposal 和 apply 结果只写入现有 `answer`。

## Capabilities

### New Capabilities

- `safe-patch-authoring`: 记录基于 evidence 的 patch proposal、pending patch 生命周期、明确确认 apply、安全 diff 校验、写入工具边界和非目标。

### Modified Capabilities

- `agent-loop-tool-execution`: 增加 Patch command / Patch intent 前置分支、`ToolInvocationContext`、`patch_apply` 工具规格和确认态审批边界。
- `chat-api`: `/chat` contract 不变；patch proposal、patch id、确认提示和 apply 结果进入现有 `answer`。
- `harness-development-workflow`: 固化 V16 的 OpenSpec、harness、review、TDD 和 V17+ non-goal 边界。

## Impact

- Code: `app/patching/**`, `app/harness/kernel.py`, `app/tools/tool_executor.py`, `app/providers/**`
- Tests: `tests/test_patch_authoring.py`, `tests/test_agent_harness_kernel.py`, `tests/test_chat_api.py`
- Docs: `README.md`, `docs/ARCHITECTURE.md`, `docs/PROGRESS.md`, `docs/FEATURE_LIST.json`, `HANDOFF_TO_NEXT_CHAT.md`
- OpenSpec / Harness: `openspec/changes/v16-safe-patch-authoring/**`, `openspec/specs/**`, `.harness/allowed_files.md`, `.harness/review_checklist.md`
- Dependencies: none.
