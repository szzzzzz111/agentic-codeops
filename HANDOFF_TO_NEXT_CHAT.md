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
- 默认 pytest、`scripts/verify.ps1` 与 CI 仍保持离线 deterministic；未创建 V24。

## 当前阻塞

- 必须提交 merge resolution，再基于最终合并状态重跑 deterministic verification、formal review
  和完整 8-call DeepSeek live gate。
- PASS attestation 产生并完成最终证据复核前，不得 archive。

## 下一步

1. 提交 merge resolution。
2. 重跑 evaluator/adjacent/full deterministic verification、formal review 与 Stage Debt Sweep。
3. 用户通过 Git-ignored live 环境运行完整 8-call DeepSeek gate。
4. PASS 后提交 attestation、复核证据、archive、merge、push；不创建 V24。
