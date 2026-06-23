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
- [x] Fallback-reason diagnostic change 后 evaluator tests：32 passed；adjacent regression：
  157 passed。
- [x] Fallback-reason diagnostic change 后 full verify：366 passed、1 skipped；OpenSpec
  strict/all：19 passed；ruff、stage docs、skill checks 与 `git diff --check` 通过。

## Review

- Gate marker: `formal_review_evidence_gate`
- Policy marker: `continuous_authorization_does_not_replace_formal_review`
- Timing marker: `formal_review_after_final_runtime_tests`
- [x] Fallback-reason diagnostic change 后 internal implementation review complete：只读取
  Grounded Answer 脱敏 audit，并在 evaluator 边界逐值 allowlist。
- [x] Independent adversarial external re-review session `ses_10dd70b89ffenCalcvMK60fWKl`
  complete：unknown/sensitive values 统一映射为 `grounded_answer_unknown`；无 P0-P3。
- [x] `manual_stage_debt_sweep_completed`：检查 fallback source/value flow、report serialization、
  historical compatibility、raw marker detection 与默认 offline verification；无新增债务。
- [x] `formal_review_findings_closed`：细粒度 failure code 替代旧泛化 code 为 intentional；
  原始 prompt/answer/evidence 不进入报告。

## Closeout

- [x] Evaluator implementation committed before live execution。
- [x] 两次历史 live failure 均保留为脱敏本地证据，不得用于当前 gate。
- [x] 第三次 run 在 commit `46687f3` 上仅 ambiguous case fallback；其余 hard gates PASS。
  Sanitized report SHA-256:
  `9cafb9311ab6eb4030f3ba16318de682c734ca9d5ada04331a1c97a36b05826d`。
- [x] `diagnostic_gap_recorded`：旧 evaluator 只记录泛化 `grounded_answer_fallback`；现改为
  使用 Grounded Answer 已脱敏 allowlist 中的具体 `fallback_reason`。
- [x] 两个独立 grounded remediation 均已归档、合并并推送。
- [ ] Real DeepSeek hard gates PASS on the updated clean commit.
- [ ] PASS attestation and final evidence review are complete.
- [ ] Change is archived, integrated and pushed.
- [x] `future_stage_only`：V24 不在本 change 内创建。
