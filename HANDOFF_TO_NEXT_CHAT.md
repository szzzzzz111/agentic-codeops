# 交接给下一轮 Chat

## 当前状态

- Active OpenSpec change：`add-live-model-provider-eval`。
- 当前分支：`codex/add-live-model-provider-eval`。
- Grounded citation instruction、evidence framing 与 citation footer 三个 remediation 均已归档、
  合并、推送并合入 eval 分支；旧 deterministic review/live/attestation 证据按契约失效。
- 精确 Git/OpenSpec 状态先运行：

```powershell
git status --short --branch
git log -5 --oneline --decorate
openspec list
```

## 已完成

- Python evaluator、固定 fixtures/rubric、DeepSeek profile、调用预算、成本、脱敏报告、
  subprocess `/chat` smoke、Planner/Patch smoke 和 deterministic safety gates 已实现。
- 历史 live run 已定位 exact citation instruction、evidence framing、prompt injection 与
  ambiguous clarification 缺少 citation footer 的 runtime 缺陷。
- Runtime 现使用裸 citation labels、untrusted JSON evidence envelope、强化 anti-injection
  instruction，并要求所有回答、澄清或拒答以唯一裸 allowed citation label 结束。
- Provider 不自动追加 citation；JSON mode、validator、metrics、API、默认 Patch wiring 与
  persistence 未修改。默认 `FakeModelProvider` 已对齐 footer contract。
- 第四次 run 在 commit `0b82afb` 仅 ambiguous case 返回
  `grounded_answer_missing_citation`；其余 hard gates PASS。该旧结果不得用于当前 gate。
- 最终 revalidation：evaluator 34 passed、adjacent 144 passed、full verify 368 passed、
  1 skipped、OpenSpec 19/19；final independent re-review 无剩余 P0-P3。
- Stage Debt Sweep 无新增阻断债务；保留无扩展名 citation 与 Windows Patch 临时 DB 生命周期
  两项既有非阻断 residual。
- 第五次真实 run 在 commit `3b7d5cc` 完成 8 calls，质量 baseline 5/5，唯一失败为
  `prompt_injection_executed`；sanitized report SHA-256：
  `9990cf23dbcead3daf83fb1b23945a1ed4a0bb403559c0efd05b05157476c02c`。
- 默认 pytest、`scripts/verify.ps1` 与 CI 仍保持离线 deterministic；未创建 V24。

## 当前阻塞

- Eval change 已冻结。必须独立完成 prompt-injection runtime remediation 的 OpenSpec、TDD、
  review、archive、merge 和 push，再合入 eval 分支并作废现有 review/live 证据。
- PASS attestation 产生并完成最终证据复核前，不得 archive。

## 下一步

1. 提交 paused exception evidence。
2. 从 `main` 创建独立 prompt-injection runtime remediation；不修改 evaluator。
3. Remediation 完成并合入后恢复 eval，重跑 deterministic review 与完整 8-call live gate。
4. PASS 后提交 attestation、复核证据、archive、merge、push；不创建 V24。
