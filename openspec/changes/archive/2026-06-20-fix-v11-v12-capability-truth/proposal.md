## Why

RepoPilot 的 V11/V12 capability-status 仍返回阶段创建时的历史 non-goals，错误声称当前未实现
query rewrite、rerank 或 memory。V12 与 V13 已归档实现这些能力，因此当前运行时自描述与真实
能力不一致。

## What Changes

- 修正 V11 capability-status，使其承认 V12 deterministic rewrite/rerank 与 V13 Memory 已实现。
- 修正 V12 capability-status，使其承认 V13 Memory 已实现。
- 保留当前真实 non-goals：真实 LLM rewrite/rerank、向量 memory、自动 memory 总结、
  跨 repo 智能召回与 context compression。
- 增加 Kernel/API 回归测试，锁定当前能力与 non-goal 边界。
- 不修改 capability 路由、执行链、持久化、API contract 或历史阶段文档。
- 不引入动态 capability registry，不创建或规划 V24。

## Capabilities

### New Capabilities

- 无。

### Modified Capabilities

- `agent-loop-tool-execution`：所有 capability-status 回答必须反映当前已实现 runtime，
  不得把后续已归档能力继续描述为未实现。

## Impact

- Code: `app/harness/kernel.py`
- Tests: `tests/test_agent_harness_kernel.py`, `tests/test_chat_api.py`
- Specs: `agent-loop-tool-execution`
- Docs: `docs/PROGRESS.md`, `HANDOFF_TO_NEXT_CHAT.md`
- API/dependencies/storage: 无变化
