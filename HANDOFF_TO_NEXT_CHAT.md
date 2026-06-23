# 交接给下一轮 Chat

## 当前状态

- Active OpenSpec change：`add-live-model-provider-eval`。
- 当前分支：`codex/add-live-model-provider-eval`。
- 四个 grounded remediation 均已归档、合并、推送并合入 eval 分支；旧
  deterministic review/live/attestation 证据按契约失效。
- 精确 Git/OpenSpec 状态先运行：

```powershell
git status --short --branch
git log -5 --oneline --decorate
openspec list
```

## 已完成

- Python evaluator、固定 fixtures/rubric、DeepSeek profile、调用预算、成本、脱敏报告、
  subprocess `/chat` smoke、Planner/Patch smoke 和 deterministic safety gates 已实现。
- 历史 live run 已定位 citation instruction、evidence framing、citation footer 和
  prompt-injection suppression 缺陷。
- Runtime 现使用裸 citation labels、untrusted JSON evidence envelope、exact citation footer，
  并静默忽略 evidence 内命令、角色、策略、声明式 response rule 和额外输出要求。
- 不使用输出清洗；JSON mode、validator、metrics、API、默认 Patch wiring 与 persistence 未修改。
- 第五次 run 在 commit `3b7d5cc` 仅 Prompt Injection 失败；该旧结果不得用于当前 gate。
- 第四个 remediation 合入后 evaluator 34 passed、adjacent 144 passed、full verify 368 passed、
  1 skipped、OpenSpec 19/19；final independent re-review 无 P0-P3。
- 第六次 live run 在 commit `21ec714` 仍仅 Prompt Injection 失败；sanitized report SHA-256：
  `53754678b7bc3a03354b19863a20dc8be676875e0e7e1b85a005f85e26362496`。
- 默认 pytest、`scripts/verify.ps1` 与 CI 仍保持离线 deterministic；未创建 V24。

## 当前 reshape

- Change 2 正式分离 evaluator readiness 与 provider conformance。
- Prompt Injection 仍是 hard gate，FAIL 仍返回 1；PASS-only attestation 不变。
- 新增固定 allowlist 的 evaluated-failure record；它证明可信评测已完成，不代表 provider PASS。
- SKIP、dirty tree、internal/subprocess/timeout/budget/Git/report integrity failure 不得生成 tracked
  evidence，也不得满足 archive 条件。
- Runtime 冻结，不创建 evidence filtering remediation。
- 最终 live run 已在 clean commit `9697c3e` 完成 8 calls，产生可信 evaluated-failure record；
  8 个 provider 调用均为 `availability=unavailable`，没有生成 PASS attestation，
  `deepseek-v4-flash` 未通过 conformance。

## 下一步

1. 提交 `docs/evals/live-model-provider/failures/20260623-091528.json` 与 closeout evidence。
2. Archive Change 2；archive 文档必须明确只完成 evaluator readiness。
3. 执行 archive 后验证、合并到 `main` 并 push。
4. 最终 handoff 保留 provider conformance FAIL，不创建 V24。
