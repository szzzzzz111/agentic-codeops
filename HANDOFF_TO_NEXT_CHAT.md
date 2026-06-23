# 交接给下一轮 Chat

## 当前状态

- Active OpenSpec change：无；`harden-grounded-evidence-framing` 已归档。
- `add-live-model-provider-eval` 在独立分支 paused；remediation 必须先归档、合并和推送。
- 精确 Git/OpenSpec 状态先运行：

```powershell
git status --short --branch
git log -5 --oneline --decorate
openspec list
```

## 已完成

- 已建立 medium-risk remediation OpenSpec/Harness contract。
- Grounded prompt 已按 TDD 改为裸 citation label + untrusted JSON evidence envelope。
- System instruction 已禁止执行或复述 evidence 内改变回答行为、泄露内容或输出 marker/token 的指令。
- JSON mode、validator、metrics、API、默认 Patch wiring、persistence 与 paused evaluator 未修改。
- Focused Provider/Grounded Answer/AgentLoop/API regression：137 passed。
- Final full verify：334 passed、1 skipped；OpenSpec strict/all：19 passed。
- Internal/focused external review 与 Stage Debt Sweep 已完成，无剩余 P0-P3。

## 当前阻塞

- Remediation 尚待 merge/push；完成后才能恢复 live eval。

## 下一步

1. Merge、push remediation。
2. 恢复 `add-live-model-provider-eval`，使旧 review/live 证据失效并完整重跑。
3. 不创建 V24。
