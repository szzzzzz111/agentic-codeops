## Why

RepoPilot 的 patch capability-status 仍停留在 V18，错误声称 Persistent Audit / Recovery 和
Worktree Isolation 未实现；同时 README 与长期 spec 暗示真实 Patch Authoring provider 已可通过
环境配置接入默认应用，但当前 AgentLoop 实际始终装配 `FakePatchAuthoringProvider`。这两处漂移会
直接损害演示、面试和运行时自描述的可信度。

## What Changes

- 修复 patch capability-status，使其准确概括 V16-V23 已实现能力与当前 non-goals。
- 增加 Kernel/API 回归测试，防止后续阶段再次把旧能力状态锁进测试。
- 修正 Safe Patch Authoring 文档与长期规格：`ModelPatchAuthoringProvider` 是可注入实现边界，
  默认应用装配尚未提供环境变量启用入口。
- 保持默认 fake provider、patch apply、worktree、verification、audit、API contract 和权限边界不变。
- 不接线真实 patch provider，不创建 V24，不处理检索性能或其他 Portfolio Readiness 债务。

## Capabilities

### New Capabilities

- 无。

### Modified Capabilities

- `agent-loop-tool-execution`：capability-status 必须反映当前已实现阶段，不能返回被后续阶段推翻的
  历史 non-goal。
- `safe-patch-authoring`：明确真实 patch provider 的当前装配边界，禁止把可注入类写成默认应用已支持
  环境配置启用。

## Impact

- Code: `app/harness/kernel.py`
- Tests: `tests/test_agent_harness_kernel.py`, `tests/test_chat_api.py`
- Specs: `agent-loop-tool-execution`, `safe-patch-authoring`
- Docs: `README.md`, `docs/ARCHITECTURE.md`, `docs/PROGRESS.md`,
  `HANDOFF_TO_NEXT_CHAT.md`
- API/dependencies/storage: 无变化
