# 当前 Harness 写入边界

Active OpenSpec change：`revalidate-deepseek-provider-conformance`。风险级别：high。当前状态：
paused after trustworthy conformance FAIL。

`classify-live-eval-transport-blockers` remediation 已归档并合回本分支；它修正了 live evaluator 对
transport/sandbox/provider-contact blocker 的分类、脱敏诊断和 tracked evidence 边界。

## 当前允许修改

- `openspec/changes/revalidate-deepseek-provider-conformance/**`
- `.harness/allowed_files.md`
- `.harness/review_checklist.md`
- `docs/PROGRESS.md`
- `HANDOFF_TO_NEXT_CHAT.md`
- 最新有效 conformance FAIL 后由 runner exclusive-create 的 pause-site evidence：
  `docs/evals/live-model-provider/failures/20260624-110532.json`
- 仅用于记录 remediation 合回事实的 archived change task/doc：
  `openspec/changes/archive/2026-06-24-classify-live-eval-transport-blockers/**`

## 禁止修改 / 禁止行为

- 不修改 `app/**` runtime、fixtures、rubric、profile、pricing 或 `scripts/verify.ps1`。
- 不修改默认 Patch wiring、`/chat` contract、默认 CI 或公开 API。
- 不 retry，不切换模型，不增加 live case，不发送额外真实 provider 诊断请求。
- 不降低 Prompt Injection、citation、secret、schema、metrics、finish reason 或 usage hard gate。
- 不覆盖、删除或改写历史 attestation/evaluated-failure record。
- 不把旧 `docs/evals/live-model-provider/failures/20260624-013028.json` 表示为 provider certification 或可靠 conformance FAIL。
- 不把最新 `docs/evals/live-model-provider/failures/20260624-110532.json` 表示为 provider certification 或完成态 evidence；它只是当前 revalidation 分支的可信 conformance FAIL pause-site evidence。
- 不打印、提交或持久化 API key、完整 URL、prompt、EvidencePack、原始回答、diff、raw exception、traceback、reasoning content、原始 fingerprint 或 HTTP payload。
- 不创建或规划 V24。
