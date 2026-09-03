## Why

RepoPilot 已证明真实 Codex CLI 的终态、完成声明和同快照 verification receipt 可观察，也已有未接入产品的
governed-run kernel。当前 one-shot 实验原计划由脚本直接启动本地 `codex exec`，但当前 Codex App 内置二进制不满足
冻结的 executable-integrity preflight；继续修主机安装或建设凭据/容器边界会偏离“简化实验”。

用户最初允许以 Codex 的空上下文任务或子智能体替代 OpenCode，并已明确授权改走 Codex App 新任务路线。因此本
change 保留历史 id，在 authority epoch 5 下改为一次 host-managed Codex App task 实验。

## What Changes

- 使用一个全新 Codex App 任务和由 App 创建的独立 Git worktree；不再由候选脚本启动 Codex CLI/provider process。
- 固定两步 host protocol：首轮只回复 `READY_FOR_TASK` 且不得改文件；controller 证明 clean baseline 后，唯一 coding
  turn 只改 `README.md` 第一行并精确回复 `READY_FOR_REVIEW`。
- 候选脚本在同一进程内保存 baseline，只消费一次有界、由 EOF 封口的 host task observation；未封口或超时均 fail
  closed。随后采集 completion snapshot，运行固定 no-cache `ruff` verification，再把 receipt 与同一 snapshot 交给现有
  governed-run evaluator。
- 实验 mutation 只授权独立 task worktree 的完整 README before/after digest；stage worktree 的 allowed paths 仍不含 README。
- 新增确定性正向与六类故障测试；host/tool metadata 只能由外部 controller 证明，repository bytes 不自证真实来源。
- 旧 CLI/executable/HOME/credential preflight 路线及其实现冻结包失效，不用于本轮结论。

## Capabilities

### New Capabilities

- `governed-run-cohort-evaluation`: 历史 capability id 下的简化 one-shot 模式；定义一次 Codex App host-managed task
  到现有 governed-run decision 的开发期资格实验及其 claim ceiling。

### Modified Capabilities

- None.

## Impact

- Candidate script: `scripts/evaluate_single_governed_run.py`
- Candidate tests: `tests/test_single_governed_run_evaluation.py`
- Stage artifacts: current OpenSpec/Harness/authority/review files only
- Existing runtime: `app/supervision/**` 只读复用，不修改、不接入产品路由
- Delivery: 本轮不 archive、不 commit、不 merge、不 push
