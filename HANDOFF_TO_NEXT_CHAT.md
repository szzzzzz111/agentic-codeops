# 交接给下一轮 Chat

## 当前状态

- Active OpenSpec change：`add-live-model-provider-eval`。
- 当前分支：`codex/add-live-model-provider-eval`。
- `harden-grounded-citation-instruction` remediation 已归档、合并并推送到 `main`，现已合入
  eval 分支；旧 deterministic review/live/attestation 证据按契约失效。
- 精确 Git/OpenSpec 状态先运行：

```powershell
git status --short --branch
git log -5 --oneline --decorate
openspec list
```

## 已完成

- Python evaluator、固定 fixtures/rubric、DeepSeek profile、调用预算、成本、脱敏报告、
  subprocess `/chat` smoke、Planner/Patch smoke 和 deterministic safety gates 已实现。
- 旧真实 run 完成 8 次调用并定位 grounded citation instruction 缺陷；该结果只作历史失败证据。
- 独立 remediation 已要求模型逐字复制 exact citation label，并把 evidence 声明为
  untrusted data；validator、JSON mode、metrics、API 和默认 Patch wiring 未修改。
- Remediation merge 后 evaluator tests 31 passed、adjacent regression 155 passed、full verify
  363 passed、1 skipped；OpenSpec strict/all 19 passed。
- Final internal/external review 与 Stage Debt Sweep 已完成，无剩余 P0-P2；Prompt Injection
  marker 现在会在 citation fallback 前从内存中的 provider response 被识别，但不会持久化原始输出。
- Updated real DeepSeek run 在 clean commit `3dfd06d` 完成 8 calls；Provider metrics、
  Planner/Patch/no-answer/secret filtering 通过，但 grounded citation 与 prompt injection 失败。
- 默认 pytest、`scripts/verify.ps1` 与 CI 仍保持离线 deterministic；未创建 V24。

## 当前阻塞

- Eval change 已 paused；必须先独立完成 grounded evidence framing remediation，再基于新的
  clean commit 重跑 deterministic review 与完整 DeepSeek live gate。
- PASS attestation 产生并完成最终证据复核前，不得 archive。

## 下一步

1. 独立创建并完成 grounded evidence framing remediation。
2. Archive、merge、push remediation 后恢复 eval branch。
3. 重跑 deterministic review 与完整 8-call DeepSeek gate。
4. PASS 后提交 attestation、复核证据、archive、merge、push；不创建 V24。
