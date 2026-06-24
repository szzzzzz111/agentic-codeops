# 当前 Review 清单

Active change：`classify-live-eval-transport-blockers`。风险级别：high。

## Scope

- [x] 仅修 live evaluator 的 transport/sandbox/provider-contact blocker 分类与脱敏诊断。
- [x] 保持历史 evidence 不可变，不回改 paused revalidation artifact。
- [x] PASS attestation 仍是唯一认证证据；transport blocker 不生成 tracked conformance evidence。
- [x] Conformance FAIL 只有在所有 required live provider attempts 都具备可评价 provider contact 时才允许 evaluated-failure record。
- [x] Plan review P1 fixed：partial provider contact 不能证明 round-level evaluability；任一 required attempt blocked 则整轮 transport/integrity blocked。
- [x] Plan review P2 fixed：missing network confirmation = `SKIP ... live_network_not_confirmed` / exit 0；during-run transport blocker = `BLOCKED ... transport_blocked` / exit 1；runner bug = `ERROR ...` / exit 2。
- [x] `REPOPILOT_LIVE_NETWORK_CONFIRMED=1` 只表示操作者显式声明/授权，不证明技术网络可达。
- [x] 默认 verify/CI 保持离线 deterministic。
- [x] 不创建 V24。

## Planning

- [x] OpenSpec proposal/design/spec/tasks 与 Harness 边界完成 internal review；diagnostics 从既有 provider audit 派生，不修改 `app/**`。
- [x] OpenSpec strict/all、stage docs checks 与 `git diff --check` 通过：`classify-live-eval-transport-blockers` valid，OpenSpec 21/21，stage docs valid，diff check clean。
- [ ] 用户确认后才进入 TDD implementation。

## Implementation / Verification

- Gate marker: `formal_review_evidence_gate`
- Policy marker: `continuous_authorization_does_not_replace_formal_review`
- Timing marker: `formal_review_after_final_runtime_tests`
- [ ] RED tests cover redacted transport metadata, all-unavailable blocker, partial-contact blocker, full-contact conformance FAIL, live shell guard and no tracked evidence.
- [ ] Focused evaluator tests 与 full deterministic verify 通过。
- [ ] Internal review covers evidence lifecycle、redaction、shell guard and historical evidence immutability.
- [ ] Independent adversarial review covers false conformance FAIL, secret leakage and default network isolation.
- [ ] `manual_stage_debt_sweep_completed`：仅检查 changed evaluator paths、PowerShell entrypoint 和直接依赖。
- [ ] `formal_review_findings_closed`。
- [ ] Archive/merge/push 仅在 deterministic verification、formal review 和 OpenSpec archive sync 通过后执行。
- [x] `future_stage_only`：V24 不在本 change 内创建。
