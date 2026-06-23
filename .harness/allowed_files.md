# 当前 Harness 写入边界

Active OpenSpec change：`add-live-model-provider-eval`。风险级别：high。

`harden-grounded-citation-instruction` 与 `harden-grounded-evidence-framing` remediation
均已归档、合并并推送到 `main`，当前 eval change 已恢复。由于 runtime 再次变化，旧
deterministic review、live result 与 attestation 证据全部失效。

Paused exception：commit `0b82afb` 的真实 run 完成 8 calls，仅 ambiguous case 稳定返回
`grounded_answer_missing_citation`。当前 change 再次冻结，等待独立 grounded citation footer
remediation。

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
- 不修改旧失败报告；新 live gate 必须从更新后的 clean tracked commit 完整重跑。
- 不保存 API key、完整 URL、prompt、EvidencePack、原始回答、原始 diff、reasoning content
  或原始 system fingerprint。
- 不创建或规划 V24。
