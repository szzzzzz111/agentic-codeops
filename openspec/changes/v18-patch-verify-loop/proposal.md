## Why

V16 已能基于 repo evidence 创建 pending patch 并在明确确认后受控 apply；V17 已能在明确验证请求下运行固定白名单验证命令。当前缺口是两者不能在一个明确用户意图下形成可观察闭环，用户需要分别 apply 和 verify，且系统没有表达 apply 后验证失败时的安全下一步。

V18 提供最小 Patch + Verify Loop：只在用户发送明确组合确认时串联 `patch_apply` 和 `verification_run`，不扩大到持久审计、worktree 或自动修复。

## What Changes

- 新增明确组合确认解析，例如 `确认 patch patch_xxx 并运行验证`、`应用 patch patch_xxx 并运行 pytest`、`confirm patch patch_xxx and run verify`。
- 组合确认必须完整解析 `patch_id` 和 verification label；半解析、缺失 label、非法 label、附加参数或 shell 语法必须整体拒绝，且不得 apply。
- AgentLoop 在 Patch command 分支内优先处理组合确认，顺序为组合确认、纯 verification intent、capability-status/repo_search。
- apply 成功后才生成独立 verification `ToolInvocationContext`，并继续通过 `PermissionPolicy -> ApprovalGate -> ToolExecutor.verification_run` 执行。
- `/chat` 顶层 contract 保持不变，组合摘要只进入 `answer` 和安全 `tool_calls`。
- V18 不持久化 verification result，不自动生成后续 patch，不 commit/push，不创建 worktree，不执行任意 shell。

## Capabilities

### New Capabilities

- `patch-verify-loop`

### Modified Capabilities

- `safe-patch-authoring`
- `verification-runner`
- `agent-loop-tool-execution`
- `chat-api`
- `harness-development-workflow`

## Impact

- Code: `app/harness/kernel.py`, `app/patching/`, `app/verification/`
- Tests: `tests/test_patch_authoring.py`, `tests/test_verification_runner.py`, `tests/test_agent_harness_kernel.py`, `tests/test_chat_api.py`
- Docs: `.harness/allowed_files.md`, `.harness/review_checklist.md`, `README.md`, `docs/ARCHITECTURE.md`, `docs/PROGRESS.md`, `docs/FEATURE_LIST.json`, `HANDOFF_TO_NEXT_CHAT.md`
