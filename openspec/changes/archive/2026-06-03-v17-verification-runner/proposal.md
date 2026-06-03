## Why

RepoPilot V16 已能在用户明确确认后通过受控 `patch_apply` 应用 unified diff，但系统仍不能执行验证命令。用户需要离开 `/chat` 手动运行 `pytest`、`ruff check .` 或 `scripts/verify.ps1`，导致“生成 patch -> apply -> 验证”的工程闭环仍缺少中间层。

V17 交付 Verification Runner：把验证命令执行收口到明确 intent、白名单命令、权限审批、统一 ToolExecutor、timeout、输出截断和脱敏摘要内。它是 V18 Patch + Verify Loop 的前置能力，但本阶段不自动串联 patch 和 verify。

## What Changes

- 新增 `verification-runner` capability，定义明确验证请求、白名单命令、执行边界、输出摘要、错误行为和非目标。
- AgentLoop 在 Patch command / Patch intent 之后、capability-status / repo_search 之前处理 Verification intent。
- 新增验证命令白名单，初始支持固定标签 `pytest`、`ruff` 和 `verify`。
- 新增 `verification_run` 工具规格和执行入口，必须经过 `ToolRegistry -> PermissionPolicy -> ApprovalGate -> ToolExecutor`。
- 新增本地 runner，使用 argv list 执行白名单命令，限制 cwd、timeout、输出截断和脱敏。
- `/chat` 顶层响应 contract 保持不变，验证状态和摘要只写入现有 `answer` 与安全 `tool_calls` 摘要。

## Capabilities

### New Capabilities

- `verification-runner`: 记录受控验证命令解析、白名单 registry、执行边界、摘要输出、红线和非目标。

### Modified Capabilities

- `agent-loop-tool-execution`: 增加 Verification intent 前置分支、`verification_run` 工具规格、确认态审批边界和 ToolExecutor 执行路径。
- `chat-api`: `/chat` contract 不变；验证结果摘要进入现有 `answer`。
- `harness-development-workflow`: 固化 V17 的 OpenSpec、harness、review、TDD 和 V18+ non-goal 边界。

## Impact

- Code: `app/verification/**`, `app/harness/kernel.py`, `app/tools/tool_executor.py`
- Tests: `tests/test_verification_runner.py`, `tests/test_agent_harness_kernel.py`, `tests/test_chat_api.py`
- Docs: `README.md`, `docs/ARCHITECTURE.md`, `docs/PROGRESS.md`, `docs/FEATURE_LIST.json`, `HANDOFF_TO_NEXT_CHAT.md`
- OpenSpec / Harness: `openspec/changes/v17-verification-runner/**`, `.harness/allowed_files.md`, `.harness/review_checklist.md`
- Dependencies: none.
