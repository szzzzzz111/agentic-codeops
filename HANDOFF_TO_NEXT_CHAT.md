# 交接给下一轮 Chat

## 当前状态

- Active OpenSpec change：`add-live-model-provider-eval`。
- 当前分支：`codex/add-live-model-provider-eval`。
- Grounded citation instruction 与 evidence framing 两个 remediation 均已归档、合并、推送并
  合入 eval 分支；旧 deterministic review/live/attestation 证据按契约失效。
- 精确 Git/OpenSpec 状态先运行：

```powershell
git status --short --branch
git log -5 --oneline --decorate
openspec list
```

## 已完成

- Python evaluator、固定 fixtures/rubric、DeepSeek profile、调用预算、成本、脱敏报告、
  subprocess `/chat` smoke、Planner/Patch smoke 和 deterministic safety gates 已实现。
- 历史 live run 已定位 exact citation instruction、方括号 framing 与 prompt injection 缺陷。
- Runtime 现使用裸 citation labels、untrusted JSON evidence envelope 和强化 anti-injection
  instruction；JSON mode、validator、metrics、API 与默认 Patch wiring 未修改。
- Evidence-framing remediation merge 后 evaluator tests 31 passed、adjacent regression
  157 passed、full verify 365 passed、1 skipped；OpenSpec strict/all 19 passed。
- 第三次真实 run 仅 ambiguous case fallback；其余 hard gates PASS。Evaluator 已补充逐值
  allowlist 的脱敏 fallback reason 诊断。
- Final evaluator tests 32 passed、adjacent regression 157 passed、full verify 366 passed、
  1 skipped；OpenSpec strict/all 19 passed；final re-review 无 P0-P3。
- 默认 pytest、`scripts/verify.ps1` 与 CI 仍保持离线 deterministic；未创建 V24。

## 当前阻塞

- 必须基于新 clean commit 重新运行完整 DeepSeek live gate。
- PASS attestation 产生并完成最终证据复核前，不得 archive。

## 下一步

1. 完成 merge conflict resolution commit。
2. 重跑 evaluator/adjacent/full deterministic verification 与 formal review。
3. 用户重新提供 Git-ignored live 环境配置后，运行完整 8-call DeepSeek gate。
4. PASS 后提交 attestation、复核证据、archive、merge、push；不创建 V24。
