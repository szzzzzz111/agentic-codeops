# 当前 Review 清单

Active change：`add-live-model-provider-eval`。风险级别：high。

## Scope

- [x] 默认 verify、CI 和普通 pytest 保持离线 deterministic。
- [ ] `/chat` smoke 证明 import-time 默认启动链使用真实 provider。
- [ ] Grounded Answer、Planner 与显式注入 Patch provider 均经过真实 smoke。
- [x] 固定评测集覆盖质量、安全、结构和 secret filtering。
- [x] 报告、成本与 attestation 使用 allowlist 且不泄露敏感内容。
- [x] 不修改 runtime、默认 Patch wiring、API contract 或 V24。

## TDD And Verification

- [x] RED/GREEN evidence covers environment, profile, budget, timeout, rubric, cost, secret filtering,
  subprocess wiring, reports and attestation.
- [x] Remediation merge 后 evaluator tests：30 passed；Provider/Grounded Answer/Planner/Patch/
  AgentLoop/API adjacent regression：155 passed。
- [x] Remediation merge 后 full verify：362 passed、1 skipped；OpenSpec strict/all：19 passed；
  ruff、stage docs、skill checks 与 `git diff --check` 通过。

## Review

- Gate marker: `formal_review_evidence_gate`
- Policy marker: `continuous_authorization_does_not_replace_formal_review`
- Timing marker: `formal_review_after_final_runtime_tests`
- [ ] Remediation merge 后重新执行 internal implementation review。
- [ ] Remediation merge 后重新执行 independent adversarial external review。
- [ ] `manual_stage_debt_sweep_completed`
- [ ] `formal_review_findings_closed`

## Closeout

- [x] Evaluator implementation committed before live execution。
- [x] 旧 run 在 commit `a842ca1` 完成 8 calls 并暴露 citation instruction 缺陷；该结果与
  SHA-256 `3d90c478b4cc91cefc74c6d22436be6589dfc8b8dcc58a93834e64733924bc2a`
  仅保留为历史失败证据，不得用于当前 gate。
- [x] 独立 remediation `2026-06-22-harden-grounded-citation-instruction` 已归档、合并并推送。
- [ ] Real DeepSeek hard gates PASS on the updated clean commit.
- [ ] PASS attestation and final evidence review are complete.
- [ ] Change is archived, integrated and pushed.
- [x] `future_stage_only`：V24 不在本 change 内创建。
