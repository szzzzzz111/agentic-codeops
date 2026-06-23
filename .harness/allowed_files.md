# 当前 Harness 写入边界

当前无 active OpenSpec change。`add-live-model-provider-eval` 已归档、合并并推送。

## 当前允许修改

- 在下一阶段经用户确认并创建独立 OpenSpec change 前，仅允许必要的仓库状态检查与文档纠错。
- 新阶段必须先同步本文件与 `.harness/review_checklist.md`，再修改 runtime、tests 或 evaluator。

## 禁止修改 / 禁止行为

- 不在无 active change 状态下继续扩展 Provider runtime、evaluator、fixture、rubric 或 profile。
- 不把 tracked evaluated-failure record 表示为 attestation、PASS 或 provider certification。
- 不把默认 pytest、CI 或 `scripts/verify.ps1` 改成依赖网络、密钥或真实模型输出。
- 不创建或规划 V24，除非用户明确启动新的阶段规划。
