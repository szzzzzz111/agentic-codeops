## Why

`revalidate-deepseek-provider-conformance` 在 transport blocker 修正后得到可信 live FAIL：
所有 provider-backed case 都已真实触达 DeepSeek，唯一失败 gate 为
`prompt_injection_executed`。这说明当前 grounded-text prompt contract 仍不足以让
`deepseek-v4-flash` 稳定把 repository evidence 中的敌意指令当作数据处理。

本 change 只修复 Grounded Answer 的 prompt-injection live 行为，使安全 hard gate 有机会在
后续 revalidation 中通过；不修改 evaluator、fixture、rubric、profile、gate 或认证证据语义。

## What Changes

- 调整 `grounded_text` 的 provider prompt contract，让模型必须把 evidence 分为“可用于回答的仓库事实”和“不可执行的 evidence-borne instruction”。
- 保持 citation footer、citation validator、EvidencePack、retrieval、live evaluator 和 `/chat` public contract 不变。
- 增加 deterministic RED/GREEN tests，覆盖 hostile evidence 指令、同段合法事实保留、同名合法标识符例外，以及 JSON object mode 不受影响。
- 更新 OpenSpec、Harness review checklist、进度与交接文档，记录 paused revalidation 的后续恢复边界。
- 不做 output sanitizer、marker 黑名单、evidence semantic filtering/projection、额外模型调用、retry、模型切换或 evaluator gate 降级。
- 不运行真实 live gate；live revalidation 必须在本 remediation 归档并合回 paused revalidation 分支后，由用户再次明确确认。

## Capabilities

### New Capabilities

- 无。

### Modified Capabilities

- `grounded-answer-model-provider`: 收紧 grounded-text prompt contract，使 repository evidence 中的敌意指令和其输出目标继续作为不可信数据处理，同时允许同一 evidence 中与用户问题相关的事实内容被回答。

## Impact

- Code: `app/providers/model_provider.py`
- Tests: `tests/test_model_provider.py`，必要时补充相邻 `tests/test_grounded_answer.py` / `tests/test_chat_api.py`
- Specs: `openspec/changes/harden-grounded-prompt-injection-live-behavior/specs/grounded-answer-model-provider/spec.md`
- Harness/docs: `.harness/allowed_files.md`、`.harness/review_checklist.md`、`docs/PROGRESS.md`、`HANDOFF_TO_NEXT_CHAT.md`
- No API schema, default CI, default Patch wiring, evaluator fixture/rubric/profile/pricing, or live evidence contract changes.
