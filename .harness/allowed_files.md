# 当前 Harness 写入边界

Active OpenSpec change：`revalidate-deepseek-provider-conformance`。风险级别：high。当前状态：
paused after trustworthy conformance FAIL；`harden-grounded-prompt-injection-live-behavior`
remediation 已在本分支归档，等待合回 paused revalidation 分支。

## 当前允许修改

- `openspec/changes/revalidate-deepseek-provider-conformance/**`
- `.harness/allowed_files.md`
- `.harness/review_checklist.md`
- `docs/PROGRESS.md`
- `HANDOFF_TO_NEXT_CHAT.md`
- archived remediation：
  `openspec/changes/archive/2026-06-24-harden-grounded-prompt-injection-live-behavior/**`
- 长期 spec archive sync：
  `openspec/specs/grounded-answer-model-provider/spec.md`

## 禁止修改 / 禁止行为

- 不在 active revalidation change 内继续修改 runtime、fixtures、rubric、profile、pricing 或 live evaluator。
- 不修改 `scripts/run_live_model_eval.ps1`、`scripts/verify.ps1`、默认 CI、`/chat` public contract 或默认 Patch wiring。
- 不降低 Prompt Injection、citation、secret、schema、metrics、finish reason 或 usage hard gate。
- 不覆盖、删除或改写历史 attestation/evaluated-failure record。
- 不把 `docs/evals/live-model-provider/failures/20260624-110532.json` 表示为 provider certification 或完成态 evidence；它只是旧 runtime 下的可信 conformance FAIL pause-site evidence。
- 归档 remediation 合回后，旧 `20260624-110532` live evidence 对 certification 解释必须标记为 stale，因为 runtime prompt 已变化。
- 不在 remediation archive/merge closeout 中运行真实 live gate；renewed live gate 必须回到 `revalidate-deepseek-provider-conformance` 分支，由用户明确确认后执行。
- 不 retry，不切换模型，不增加 live case，不发送额外真实 provider 诊断请求。
- 不打印、提交或持久化 API key、完整 URL、prompt、EvidencePack、原始回答、diff、raw exception、traceback、reasoning content、原始 fingerprint 或 HTTP payload。
- 不创建或规划 V24。
