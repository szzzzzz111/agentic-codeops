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
- [x] Evidence-framing remediation merge 后 evaluator tests：31 passed；adjacent regression：
  157 passed。
- [x] Evidence-framing remediation merge 后 full verify：365 passed、1 skipped；OpenSpec
  strict/all：19 passed；ruff、stage docs、skill checks 与 `git diff --check` 通过。

## Review

- Gate marker: `formal_review_evidence_gate`
- Policy marker: `continuous_authorization_does_not_replace_formal_review`
- Timing marker: `formal_review_after_final_runtime_tests`
- [x] Evidence-framing remediation merge 后 internal implementation review complete：确认
  runtime prompt tests、citation validator、raw marker detection、JSON callers、budget、metrics、
  reports 与 clean-tree binding。
- [x] Independent adversarial re-review session `ses_10dd70b89ffenCalcvMK60fWKl` complete：
  无 P0-P2；4 个 P3 均为冗余检查、脱敏诊断或固定 rubric scope 边界。
- [x] `manual_stage_debt_sweep_completed`：检查 runtime prompt/validator、evaluator cases/API
  subprocess、Planner/Patch、budget/deadline、metrics/cost、report/attestation、PowerShell 与默认
  verify；无新增阻断债务。
- [x] `formal_review_findings_closed`：API citation 由上游 strict validator 保证；subprocess
  fingerprint status 丢失不影响 gate 且原值禁止持久化；固定 ATTACK_MARKER 与编码绕过按 rubric
  scope 接受。既有 extensionless citation 与 Windows Patch DB lifecycle residual 保留。

## Closeout

- [x] Evaluator implementation committed before live execution。
- [x] 两次历史 live failure 均保留为脱敏本地证据，不得用于当前 gate。
- [x] 两个独立 grounded remediation 均已归档、合并并推送。
- [ ] Real DeepSeek hard gates PASS on the updated clean commit.
- [ ] PASS attestation and final evidence review are complete.
- [ ] Change is archived, integrated and pushed.
- [x] `future_stage_only`：V24 不在本 change 内创建。
