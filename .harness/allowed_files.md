# 当前 Harness 写入边界

Active OpenSpec change：无。`revalidate-deepseek-provider-conformance` 已归档到
`openspec/changes/archive/2026-06-24-revalidate-deepseek-provider-conformance/`。

## 当前允许修改

- archive closeout 文档：
  - `.harness/allowed_files.md`
  - `.harness/review_checklist.md`
  - `docs/PROGRESS.md`
  - `HANDOFF_TO_NEXT_CHAT.md`
- revalidation archive：
  `openspec/changes/archive/2026-06-24-revalidate-deepseek-provider-conformance/**`
- live eval long-term spec archive sync：
  `openspec/specs/live-model-provider-eval/spec.md`

## 禁止修改 / 禁止行为

- 不再修改 runtime、tests、fixtures、rubric、profile、pricing、live evaluator 或 evidence schema。
- 不修改 `scripts/run_live_model_eval.ps1`、`scripts/verify.ps1`、默认 CI、`/chat` public contract 或默认 Patch wiring。
- 不运行额外 live gate，不 retry，不切换模型，不增加 live case，不发送额外真实 provider 诊断请求。
- 不覆盖、删除或改写历史 attestation/evaluated-failure record。
- 不打印、提交或持久化 API key、完整 URL、prompt、EvidencePack、原始回答、diff、raw exception、traceback、reasoning content、原始 fingerprint 或 HTTP payload。
- 不创建或规划 V24。
