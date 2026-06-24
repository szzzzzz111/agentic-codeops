# 当前 Review 清单

Active change：`revalidate-deepseek-provider-conformance`。风险级别：high。当前状态：paused，等待用户确认是否在
network-capable shell 中重新运行一次 DeepSeek provider conformance gate。

## 已合回 remediation

- [x] `classify-live-eval-transport-blockers` 已归档并合回当前 revalidation 分支。
- [x] Transport/sandbox/provider-contact blocker 不再生成 PASS attestation 或 evaluated-failure record。
- [x] 任一 required live provider attempt 缺少可评价 provider contact 时，整轮 outcome 为 `transport_blocked`。
- [x] 缺少 `REPOPILOT_LIVE_NETWORK_CONFIRMED=1` 时 runner 在 git/provider 调用前 SKIP/0。
- [x] Local report diagnostics 只允许 `phase`、`error_class`、`status_class`，且 `error_class` 已做 safe code token 收敛。
- [x] `build_evaluated_failure_record()` 已增加 provider-contact 完整性防线。
- [x] Remediation deterministic evidence：focused evaluator tests `64 passed`；full verify `398 passed, 1 skipped`；OpenSpec all `21 passed, 0 failed`。
- [x] Remediation review：internal review、independent adversarial review 和 Stage Debt Sweep 已完成；无剩余 P0/P1 blocker。

## 当前 revalidation 边界

- [x] 旧 live artifact `docs/evals/live-model-provider/failures/20260624-013028.json` 已解释为旧 contract 下 provider-contact-unverified transport/integrity blocker 现场，不是 provider certification。
- [x] PASS attestation 仍是唯一 provider certification evidence。
- [x] 若重新运行 live gate，必须由用户明确确认 network-capable execution，并设置 `REPOPILOT_LIVE_NETWORK_CONFIRMED=1`。
- [x] 重新运行 live gate 前必须保持 clean tracked working tree。
- [x] 默认 verify/CI 仍必须离线 deterministic。
- [x] 不创建 V24。

## 下一次 live 前检查

- [ ] 用户明确确认 live/network-capable shell。
- [ ] `.env.live` 或当前 shell 提供五个必需 provider key，且不打印 value。
- [ ] 当前 process environment 显式包含 `REPOPILOT_LIVE_NETWORK_CONFIRMED=1`。
- [ ] `git status --short --branch` clean。
- [ ] `openspec validate --all` pass。
- [ ] `powershell -ExecutionPolicy Bypass -File scripts/check_stage_docs.ps1` pass。
