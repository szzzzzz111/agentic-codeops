# 当前 Harness 写入边界

Active OpenSpec change：`harden-grounded-prompt-injection-live-behavior`。风险级别：high。

当前分支从 paused `codex/revalidate-deepseek-provider-conformance` 切出；父 change 的最新可信
DeepSeek conformance FAIL 只失败于 `prompt_injection_executed`。本 remediation 只允许修复
Grounded Answer grounded-text prompt contract；不在父 revalidation change 内直接改 runtime。

## 当前允许修改

- `app/providers/model_provider.py`
- `tests/test_model_provider.py`
- 如直接需要，可修改相邻回归测试：
  - `tests/test_grounded_answer.py`
  - `tests/test_chat_api.py`
- `openspec/changes/harden-grounded-prompt-injection-live-behavior/**`
- `.harness/allowed_files.md`
- `.harness/review_checklist.md`
- `docs/PROGRESS.md`
- `HANDOFF_TO_NEXT_CHAT.md`

## 禁止修改 / 禁止行为

- 不修改 `evals/**`、live fixtures、rubric、profile、pricing 或 live evidence writer。
- 不修改 `scripts/run_live_model_eval.ps1`、`scripts/verify.ps1`、默认 CI、`/chat` public contract 或默认 Patch wiring。
- 不修改 retrieval、EvidencePack、citation validator、provider metrics、finish-reason handling、reports 或 tracked evidence schema，除非正式重新规划。
- 不做 output sanitizer、marker 黑名单、response rewriting、evidence filtering/projection/suppression 或额外模型调用。
- 不降低 Prompt Injection、citation、secret、schema、metrics、finish reason 或 usage hard gate。
- 不覆盖、删除或改写历史 attestation/evaluated-failure record。
- 不在本 remediation 内运行真实 live gate；归档并合回 revalidation 分支后，live gate 仍需用户明确确认。
- 不 retry，不切换模型，不增加 live case，不发送额外真实 provider 诊断请求。
- 不打印、提交或持久化 API key、完整 URL、prompt、EvidencePack、原始回答、diff、raw exception、traceback、reasoning content、原始 fingerprint 或 HTTP payload。
- 不创建或规划 V24。
