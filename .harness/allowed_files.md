# 当前 Harness 写入边界

Active OpenSpec change：`revalidate-deepseek-provider-conformance`。风险级别：high。

本阶段只复用已归档的 live evaluator，在新的 clean commit 上重新验证
`deepseek-v4-flash` provider conformance。现有 runtime、evaluator、fixtures、rubric、profile 和
tests 全部冻结。

## 当前允许修改

- `openspec/changes/revalidate-deepseek-provider-conformance/**`
- `.harness/allowed_files.md`
- `.harness/review_checklist.md`
- PASS 后的 `docs/evals/live-model-provider/<timestamp>.json`
- 有效 conformance FAIL 后由 runner exclusive-create 的
  `docs/evals/live-model-provider/failures/<timestamp>.json`，仅作为当前 revalidation 分支的暂停现场证据
- PASS/FAIL closeout 所需的 `docs/PROGRESS.md`
- `HANDOFF_TO_NEXT_CHAT.md`
- archive sync 产生的 `openspec/specs/live-model-provider-eval/spec.md`

## 禁止修改 / 禁止行为

- 不修改 `app/**`、`evals/**`、`tests/**`、fixtures、rubric、profile、pricing、
  `scripts/run_live_model_eval.ps1` 或 `scripts/verify.ps1`。
- 不修改默认 Patch wiring、`/chat` contract、默认 CI 或公开 API。
- 不 retry，不切换模型，不增加 live case，不发送额外诊断请求。
- 不降低 Prompt Injection、citation、secret、schema、metrics、finish reason 或 usage hard gate。
- 不覆盖、删除或改写历史 attestation/evaluated-failure record。
- 不把 FAIL、SKIP、ERROR 或 integrity failure 表示为 provider certification。
- 不把 FAIL record 用于 archive、merge 到 `main` 或 push 为完成态，除非后续正式 reshape 契约。
- 不打印、提交或持久化 API key、完整 URL、prompt、EvidencePack、原始回答/diff、
  reasoning content、原始 fingerprint 或 HTTP payload。
- 不创建或规划 V24。
