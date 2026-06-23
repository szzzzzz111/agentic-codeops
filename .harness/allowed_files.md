# 当前 Harness 写入边界

Active OpenSpec change：`add-live-model-provider-eval`。风险级别：high。

Change 正在正式 reshape：Prompt Injection 仍是 hard gate，真实 conformance FAIL 仍返回 1，
PASS-only attestation 不变；新增固定 allowlist 的 evaluated-failure record，把 evaluator readiness
与 provider conformance 分离。当前 runtime 冻结，不创建 evidence filtering remediation。

第六次真实 run 在 commit `21ec714` 完成 8 calls，质量 baseline 5/5，除
`prompt_injection_executed` 外所有 hard gates 通过。该结果证明 evaluator 能稳定捕获回答完整性
风险，但旧 runner 尚不能生成 reshaped failure record，因此实现后必须在新的 clean commit 上重跑。

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

- 不修改 `app/**` runtime、system prompt、EvidencePack、默认 Patch wiring、`/chat` contract 或
  `scripts/verify.ps1`。
- 不降低 Prompt Injection、citation、secret、schema、metrics 或 provider hard gate。
- 不改变 FAIL=1、ERROR=2、SKIP=0 的退出码语义。
- 不把 evaluated-failure record 表示为 attestation、PASS 或 provider certification。
- 不为 SKIP、profile mismatch、dirty tree、subprocess/integrity failure、timeout、预算异常、
  Git 状态变化或报告校验失败生成 tracked evidence。
- 不保存 API key、完整 URL、prompt、EvidencePack、原始回答、原始 diff、reasoning content、
  原始 fingerprint 或原始 HTTP payload。
- 不把普通 pytest、默认 CI 或默认 verify 改成依赖网络、密钥或真实模型输出。
- 不创建或规划 V24。
