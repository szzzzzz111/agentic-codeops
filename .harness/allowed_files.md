# 当前 Harness 写入边界

Active OpenSpec change：`add-live-model-provider-eval`。风险级别：high。

Paused exception：真实 DeepSeek run 在 commit `a842ca1` 上完成 8 次调用，但全部 grounded-text
case 因 citation contract 失败。当前 change 冻结 evaluator/runtime 修改，等待独立
`harden-grounded-citation-instruction` remediation 完成后恢复。

## 当前允许修改

- `openspec/changes/add-live-model-provider-eval/**`
- `.harness/allowed_files.md`
- `.harness/review_checklist.md`
- `evals/__init__.py`
- `evals/live_model_provider/**`
- `scripts/run_live_model_eval.ps1`
- `tests/test_live_model_provider_eval.py`
- `docs/evals/live-model-provider/**`
- `docs/PROGRESS.md`
- `HANDOFF_TO_NEXT_CHAT.md`

## 禁止修改 / 禁止行为

- 不修改 `app/**` runtime、默认 Patch wiring、`/chat` contract 或 `scripts/verify.ps1`。
- 不把普通 pytest、默认 CI 或默认 verify 改成依赖网络、密钥或真实模型输出。
- 不在本 change 内修复 live gate 暴露的 runtime 缺陷；需要独立 remediation change。
- Paused 期间不修改 evaluator、fixture、rubric、profile、tests 或 attestation contract。
- 不保存 API key、完整 URL、prompt、EvidencePack、原始回答、原始 diff、reasoning content
  或原始 system fingerprint。
- 不创建或规划 V24。
