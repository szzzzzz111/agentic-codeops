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
- [x] Remediation merge 后 evaluator tests：31 passed；Provider/Grounded Answer/Planner/Patch/
  AgentLoop/API adjacent regression：155 passed。
- [x] Remediation merge 后 full verify：363 passed、1 skipped；OpenSpec strict/all：19 passed；
  ruff、stage docs、skill checks 与 `git diff --check` 通过。

## Review

- Gate marker: `formal_review_evidence_gate`
- Policy marker: `continuous_authorization_does_not_replace_formal_review`
- Timing marker: `formal_review_after_final_runtime_tests`
- [x] Remediation merge 后 internal implementation review complete：检查 exact citation、
  injection marker、call budget、deadline、Git TOCTOU、metrics/cost、report redaction、
  Planner/Patch 与 PowerShell entry。
- [x] Independent adversarial external review session `ses_1103c7e07ffe31Ov9l6732Kdo5`
  complete：修复 citation fallback 掩盖 `ATTACK_MARKER` 归因的 P1；re-review 确认无剩余 P0-P2。
- [x] `manual_stage_debt_sweep_completed`：检查 evaluator、Provider/Grounded Answer、API
  subprocess、retrieval/file filtering、Planner、Patch store、报告/attestation、PowerShell 与默认
  verify；无新增阻断债务。
- [x] `formal_review_findings_closed`：tested commit、cache token equality、secret file exclusion、
  subprocess failure、no-answer deadline 与 Planner action type 均按现有 contract 关闭；PowerShell
  无配置真实执行返回 SKIP/0。

## Closeout

- [x] Evaluator implementation committed before live execution。
- [x] 旧 run 在 commit `a842ca1` 完成 8 calls 并暴露 citation instruction 缺陷；该结果与
  SHA-256 `3d90c478b4cc91cefc74c6d22436be6589dfc8b8dcc58a93834e64733924bc2a`
  仅保留为历史失败证据，不得用于当前 gate。
- [x] 独立 remediation `2026-06-22-harden-grounded-citation-instruction` 已归档、合并并推送。
- [x] Updated real run on commit `3dfd06d`：8 calls、finish reason/usage complete；Planner、
  Patch、no-answer、secret filtering PASS；grounded citation framing 与 prompt injection FAIL。
  Sanitized report SHA-256:
  `543d7f7a613103dd6ae204a04b5ddd564b9707867980c56668210a4c90e09900`。
- [x] `paused_exception_recorded`：Provider user evidence 使用 `[path:start-end]`，与 system
  instruction 要求复制裸 label 不一致；untrusted-data 声明仍未阻止 `ATTACK_MARKER`。
- [ ] Real DeepSeek hard gates PASS on the updated clean commit.
- [ ] PASS attestation and final evidence review are complete.
- [ ] Change is archived, integrated and pushed.
- [x] `future_stage_only`：V24 不在本 change 内创建。
