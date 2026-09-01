## Why

RepoPilot 已证明可以观察一次真实 Codex 运行的终态声明，并把验证回执绑定到同一 Git 快照；下一步需要把这条证据链收敛成最小、可复用且 fail-closed 的监督合同。该合同只判断是否应继续、介入、交给人处理或进入人工 review，不把 Agent 声明或测试通过提升为任务完成。

## What Changes

- 新增内部 `RunContract`、`GitSnapshot`、`AgentClaim` 与 `VerificationReceipt` 不可变数据合同，显式绑定
  run/thread/event/claim/command/snapshot identity，阻止跨 run 的旧证据误复用。
- 新增真实 Codex JSONL 事件适配器，只接受唯一且无歧义的终态与精确 `READY_FOR_REVIEW` 声明。
- 新增只读 Git snapshot collector，以受控 child environment、固定 argv、无 Git helper、timeout/output cap、
  `shell=False`、`GIT_OPTIONAL_LOCKS=0` 和两次稳定采样捕获 repository、HEAD、status、tracked diff 与包括 ignored
  文件在内的 all-untracked inventory。
- 新增纯 evaluator，穷尽输出 `continue / intervene / needs_human / ready_for_review`；所有结果的 `task_complete`
  均为 `false`、source provenance 均为 unverified，snapshot claim 只覆盖两个稳定采样端点。
- 新增确定性测试与一条真实 Agent qualification regression，覆盖 scope、dirty baseline、事件歧义、claim、verification 和 snapshot drift 的 fail-closed 行为。
- 不新增 public API、CLI、持久化 authority、Agent launcher、后台服务、自动纠偏或任何 Git 写入/交付能力。

## Capabilities

### New Capabilities

- `governed-run-contract`: 为单个真实 Coding Agent 运行定义 snapshot-bound completion claim、verification receipt 和有界人工监督决策。

### Modified Capabilities

无。

## Impact

- 新增内部 `app/supervision/` 模块和 focused tests；现有 `/chat`、CLI、ToolRegistry、provider 默认值、patch/worktree/verification 行为保持不变。
- 读取本地 Git 状态，但不修改 worktree、index、refs 或远端。
- 不增加依赖、网络默认行为或公开兼容面。
- 风险等级为 high / L3；实现前需要两席独立 plan review 和用户对完整 design/tasks/spec 决策的确认。
