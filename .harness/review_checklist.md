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
- [x] Fallback-reason diagnostic change 后 evaluator tests：32 passed；adjacent regression：
  157 passed。
- [x] 三个 runtime remediation 与 final review remediation 合入后 evaluator tests：34 passed；
  adjacent regression：144 passed。
- [x] Final full verify：368 passed、1 skipped；OpenSpec strict/all：19 passed；ruff、stage docs、
  skill checks 与 `git diff --check` 全部通过。

## Review

- Gate marker: `formal_review_evidence_gate`
- Policy marker: `continuous_authorization_does_not_replace_formal_review`
- Timing marker: `formal_review_after_final_runtime_tests`
- [x] Fallback-reason diagnostic change 后 internal/external review 确认 audit 值经逐值 allowlist，
  unknown/sensitive values 统一映射为 `grounded_answer_unknown`。
- [x] Citation-footer remediation 已完成 TDD、focused external review 与 Stage Debt Sweep；
  默认 Fake provider 和真实 provider instruction 使用同一 footer contract。
- [x] 基于三个 remediation 合入后的最终 evaluator/runtime 状态完成 internal review。
- [x] Independent adversarial external review session `ses_10d9349e0ffeNpD2V2aufI9m3a`
  初审提出 4 个 P2、4 个 P3；P2 call-count 噪声与 marker 大小写绕过已按 TDD 修复。
- [x] Final external re-review session `ses_10d8d1669ffeL4pA556DAaYLzW` 确认两项修复正确，
  无剩余 P0-P3。
- [x] `manual_stage_debt_sweep_completed`：检查 evaluator、Grounded Answer、Provider、
  Planner/Patch、API subprocess、retrieval secret boundary、报告/attestation 与默认 offline
  verification；无新增阻断债务。
- [x] `formal_review_findings_closed`：其余 external findings 经核对为设计内 probe、明确
  out-of-scope future provider concern 或既有非阻断 residual。

## Closeout

- [x] Evaluator implementation committed before live execution。
- [x] 四次历史 live failure 均保留为脱敏本地证据，不得用于当前 gate。
- [x] 第四次 run 在 commit `0b82afb` 上确认 ambiguous case 为
  `grounded_answer_missing_citation`；其余 hard gates PASS。Sanitized report SHA-256:
  `47aecb0e72c543ef0d58855824e6389077eaeec66f96c1dc3cd7a7d95d4708d`。
- [x] `paused_exception_recorded`：稳定缺失 citation 行为由独立 citation-footer remediation 修复，
  未在 eval change 内修改 runtime。
- [x] 三个独立 grounded remediation 均已归档、合并、推送并合入 eval 分支。
- [x] 第五次 live run 在 commit `3b7d5cc` 完成 8 calls：质量 baseline 5/5，除 Prompt
  Injection 外所有 hard gates PASS；sanitized report SHA-256：
  `9990cf23dbcead3daf83fb1b23945a1ed4a0bb403559c0efd05b05157476c02c`。
- [x] `paused_exception_recorded`：`prompt_injection_executed` 属于 runtime safety 缺陷；
  eval change 已冻结，不在本 change 内修改 prompt/runtime。
- [ ] Real DeepSeek hard gates PASS on the updated clean commit.
- [ ] PASS attestation and final evidence review are complete.
- [ ] Change is archived, integrated and pushed.
- [x] `future_stage_only`：V24 不在本 change 内创建。
