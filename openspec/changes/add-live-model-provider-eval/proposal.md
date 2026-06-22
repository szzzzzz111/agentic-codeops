## Why

RepoPilot 已具备真实 OpenAI-compatible Model Provider 接线，但当前验证只覆盖 mock HTTP 和
deterministic fake provider，尚未证明默认 `/chat` 启动链、Grounded Answer、Long Task Planner
与显式注入的 Patch Authoring 能在真实兼容端点上满足 citation、结构化输出、安全和指标契约。

## What Changes

- 新增独立 Python live evaluator、固定评测集、rubric、DeepSeek profile、脱敏报告和成本统计。
- 新增薄 PowerShell 入口；缺少显式 live 环境配置时明确 `SKIP`，默认验证继续离线确定性。
- 在全新 subprocess 中验证默认 `/chat` 启动 wiring，并分别验证 Grounded Answer、Long Task
  Planner 和显式依赖注入的 `ModelPatchAuthoringProvider`。
- 增加 prompt injection、无答案、secret filtering、报告脱敏、调用预算和 timeout 硬门。
- 只有真实 DeepSeek hard gates PASS 并生成 tracked attestation 后才允许归档本 change。
- 不修改 Model Provider runtime、默认 Patch wiring、`/chat` contract、默认 CI 或
  `scripts/verify.ps1`，不创建 V24。

## Capabilities

### New Capabilities

- `live-model-provider-eval`: 定义可选真实 provider smoke/eval、固定数据集、硬门、质量 baseline、
  脱敏报告、成本和归档证据。

### Modified Capabilities

- 无。

## Impact

- Code: `evals/live_model_provider/**`、`scripts/run_live_model_eval.ps1`
- Tests: `tests/test_live_model_provider_eval.py`
- Process: `.harness/allowed_files.md`、`.harness/review_checklist.md`
- Docs: `docs/PROGRESS.md`、`HANDOFF_TO_NEXT_CHAT.md`、PASS 后的
  `docs/evals/live-model-provider/*.json`
- Runtime/API: 无变更；默认验证不新增网络依赖。
