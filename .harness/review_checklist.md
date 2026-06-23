# 当前 Review 清单

Active change：`add-live-model-provider-eval`。风险级别：high。

## Scope

- [x] 默认 verify、CI 和普通 pytest 保持离线 deterministic。
- [ ] `/chat` smoke 在更新后的 clean commit 上证明 import-time 默认启动链使用真实 provider。
- [ ] Grounded Answer、Planner 与显式注入 Patch provider 在更新后的 clean commit 上均经过真实 smoke。
- [x] 固定评测集覆盖质量、安全、结构和 secret filtering。
- [x] 报告、成本与 attestation 使用 allowlist 且不泄露敏感内容。
- [x] Eval change 不修改 runtime、默认 Patch wiring、API contract 或 V24。

## TDD And Verification

- [x] RED/GREEN evidence covers environment, profile, budget, timeout, rubric, cost, secret filtering,
  subprocess wiring, reports and attestation.
- [x] Final evaluator implementation before latest runtime remediation：34 passed。
- [x] Prompt-injection remediation 合入后 evaluator tests：34 passed；adjacent regression：
  144 passed；full verify：368 passed、1 skipped。
- [x] 更新后的 OpenSpec strict/all：19 passed；ruff、stage docs、skill checks 与
  `git diff --check` 全部通过。

## Review

- Gate marker: `formal_review_evidence_gate`
- Policy marker: `continuous_authorization_does_not_replace_formal_review`
- Timing marker: `formal_review_after_final_runtime_tests`
- [x] Prompt-injection remediation 已完成 TDD、focused external review 与 Stage Debt Sweep；
  prompt-only contract 不包含 post-processing 或 evaluator 修改。
- [x] 基于第四个 runtime remediation 合入后的最终 evaluator/runtime 状态完成 internal review。
- [x] Independent adversarial external review session `ses_10d50ad3effe50HF4rpRMXvo3h`
  complete：旧证据作废、offline default、call budget、redaction 与 fixture/prompt 一致性均通过；
  无 P0-P3。
- [x] `manual_stage_debt_sweep_completed`：检查 evaluator、Prompt Injection fixture/gate、
  grounded prompt contract、JSON callers、报告/attestation 与默认 offline verification；
  无新增阻断债务。
- [x] `formal_review_findings_closed`：同名标识符仅由 prompt-contract 覆盖为已知非阻断 residual，
  真实模型服从仍由本 change 的 live gate 验证。

## Closeout

- [x] Evaluator implementation committed before live execution。
- [x] 五次历史 live failure 均保留为脱敏本地证据，不得用于当前 gate。
- [x] 第五次 run 在 commit `3b7d5cc` 上仅 Prompt Injection 失败；sanitized report SHA-256：
  `9990cf23dbcead3daf83fb1b23945a1ed4a0bb403559c0efd05b05157476c02c`。
- [x] `paused_exception_recorded`：该 failure 由独立 prompt-injection remediation 处理，
  未在 eval change 内修改 runtime。
- [x] 四个独立 grounded remediation 均已归档、合并、推送并合入 eval 分支。
- [ ] Real DeepSeek hard gates PASS on the updated clean commit.
- [ ] PASS attestation and final evidence review are complete.
- [ ] Change is archived, integrated and pushed.
- [x] `future_stage_only`：V24 不在本 change 内创建。
