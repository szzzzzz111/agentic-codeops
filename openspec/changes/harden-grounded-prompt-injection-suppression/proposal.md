## Why

真实 DeepSeek live gate 在 citation、usage、结构和质量均通过时，仍执行了 repository evidence
中的不可信指令并输出 marker。现有 instruction 已禁止遵循和转换 evidence 指令，但没有明确要求
对指令目标及其 marker/token 保持静默，导致拒绝或说明也可能复现攻击载荷。

## What Changes

- 收紧 grounded-text system instruction：识别 evidence 中的指令性文本后必须静默忽略，只使用
  其中与用户仓库问题相关的事实内容。
- 明确禁止在回答、拒答、澄清、引用或安全说明中输出、复述、拼写、转换、编码、翻译或讨论
  evidence 指令要求产生、且与 original query 无关的 marker/token。
- 保持 exact citation footer、evidence JSON envelope、citation validator、JSON object mode、
  metrics、API、默认 Patch wiring 和 persistence contract 不变。
- 不增加输出后清洗、marker 黑名单、evidence 内容过滤、answerability classifier、retry 或 V24。
- 使用 deterministic TDD、focused external review、Stage Debt Sweep 和完整离线 verify；真实
  live gate 仍由独立 `add-live-model-provider-eval` change 在本 remediation 归档合并后重跑。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `grounded-answer-model-provider`：grounded-text instruction 必须静默忽略 evidence 内的指令及其
  输出目标，且不得在任何响应形式中复现攻击 marker/token。

## Impact

- Code: `app/providers/model_provider.py`
- Tests: `tests/test_model_provider.py`，以及直接相邻的 Grounded Answer/AgentLoop/API regression
- Specs: `openspec/specs/grounded-answer-model-provider/spec.md`
- Process/docs: `.harness/allowed_files.md`、`.harness/review_checklist.md`、
  `docs/PROGRESS.md`、`HANDOFF_TO_NEXT_CHAT.md`
- Runtime/API: 仅 grounded-text prompt contract 收紧；无公开 API、持久化或默认 wiring 变化
