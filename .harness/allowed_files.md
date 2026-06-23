# 当前 Harness 写入边界

当前无 active OpenSpec change。`harden-grounded-prompt-injection-suppression` 已归档为
`2026-06-23-harden-grounded-prompt-injection-suppression`。

该 remediation 由 `add-live-model-provider-eval` 在 clean commit `3b7d5cc` 上的真实 DeepSeek
失败触发：8 calls 中仅 Prompt Injection hard gate 失败。Eval change 保持冻结；本分支只允许
收紧 grounded-text prompt contract，不得修改 evaluator 或通过输出清洗掩盖失败。

## 当前允许修改

- `openspec/changes/harden-grounded-prompt-injection-suppression/**`
- `openspec/specs/grounded-answer-model-provider/spec.md`（仅 archive sync）
- `.harness/allowed_files.md`
- `.harness/review_checklist.md`
- `app/providers/model_provider.py`
- `tests/test_model_provider.py`
- `docs/ARCHITECTURE.md`
- `docs/PROGRESS.md`
- `HANDOFF_TO_NEXT_CHAT.md`

## 禁止修改 / 禁止行为

- 不修改 `evals/**`、`tests/test_live_model_provider_eval.py`、fixture、rubric、profile、报告或
  attestation contract。
- 不增加输出后 marker 清洗、marker 黑名单、EvidencePack 过滤或 instruction classifier。
- 不修改 citation validator、evidence JSON envelope、JSON object mode、metrics、API、默认
  Patch wiring、persistence 或 `scripts/verify.ps1`。
- 不把默认 pytest、CI 或 verify 改成依赖网络、密钥或真实模型输出。
- 不在本 remediation 内运行真实 live gate；归档合并后由 eval change 完整重跑。
- 不保存 API key、prompt、EvidencePack、原始回答或 reasoning content。
- 不创建或规划 V24。
