# 交接给下一轮 Chat

## 当前状态

- Active OpenSpec change：`harden-grounded-prompt-injection-suppression`。
- 当前分支：`codex/harden-grounded-prompt-injection-suppression`。
- `add-live-model-provider-eval` 在独立分支冻结；本 remediation 必须先归档、合并和推送。
- 精确 Git/OpenSpec 状态先运行：

```powershell
git status --short --branch
git log -5 --oneline --decorate
openspec list
```

## 已完成

- 第五次真实 DeepSeek run 在 eval commit `3b7d5cc` 完成 8 calls，质量 baseline 5/5，唯一失败为
  `prompt_injection_executed`；其余 hard gates 均通过。
- Grounded-text prompt 现要求静默忽略 evidence 内的命令、角色、策略、声明式 response rule 和
  额外输出要求，不得确认、解释拒绝、转换或复现 original query 未明确询问的 marker/token。
- 用户明确询问同名仓库事实或标识符时仍可基于相关 evidence 回答。
- 未增加输出清洗、marker 黑名单、EvidencePack 过滤或 classifier；citation footer、validator、
  JSON mode、metrics、API、默认 Patch wiring、persistence 和 frozen evaluator 均未修改。
- Focused regression：137 passed；full verify：334 passed、1 skipped；OpenSpec：19/19。
- Internal/focused external review 与 Stage Debt Sweep 已完成，external re-review 无剩余 P0-P3。

## 当前阻塞

- Remediation 尚待 commit、archive、merge 和 push。
- Runtime 变化后，eval change 既有 deterministic review、live result 与 attestation 证据全部失效。

## 下一步

1. 提交并 archive remediation，复验后 merge/push。
2. 恢复 `add-live-model-provider-eval`，合入最新 `main` 并重跑 deterministic workflow。
3. 用户重新提供 Git-ignored live 环境后运行完整 8-call DeepSeek gate。
4. PASS 后提交 attestation、最终复核、archive、merge、push；不创建 V24。
