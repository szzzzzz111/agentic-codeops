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
- [x] Evaluator tests 30 passed；focused provider/answer/Planner/Patch/AgentLoop/API regression
  181 passed。
- [x] Full `scripts/verify.ps1`：361 passed、1 skipped；ruff、stage docs 与 skill checks 通过。
- [x] OpenSpec strict/all validation：19 passed；stage checks 与 `git diff --check` 通过。

## Review

- Gate marker: `formal_review_evidence_gate`
- Policy marker: `continuous_authorization_does_not_replace_formal_review`
- Timing marker: `formal_review_after_final_runtime_tests`
- [x] Internal plan review confirms the high-risk contract, eight-call budget, PASS-only
  attestation, no-key archive blocker and no runtime scope drift.
- [x] Formal implementation review postdates final evaluator/test changes；修复 returned-model /
  usage consistency、global deadline、secret positive control、negative usage 和 Git TOCTOU。
- [x] Independent adversarial external review 使用 `opencode/deepseek-v4-flash-free` 检查
  secret/report leakage、false PASS、wiring、timeout、budget、cost 和 attestation；re-review
  确认所有 P0/P1 关闭。
- [x] `manual_stage_debt_sweep_completed`：检查 evaluator、runner、PowerShell、tests 及直接依赖的
  Model Provider、Grounded Answer、Planner、PatchManager/store、API global wiring、
  retrieval/file filtering、`.gitignore` 和默认 verify。
- [x] `formal_review_findings_closed`：所有 P0/P1 已关闭；P2 为版本化价格/严格 API contract 等
  设计约束，及 Windows Patch 临时 DB 依赖 CPython `gc.collect()` 的非阻断 residual。

## Closeout

- [x] Evaluator implementation is committed before live execution；clean-tree live entry returned
  SKIP because all five required environment variables were absent.
- [ ] Real DeepSeek hard gates PASS on the recorded clean commit.
- [ ] PASS attestation and final evidence review are complete.
- [ ] Change is archived, integrated and pushed.
- [ ] `future_stage_only`：V24 不在本 change 内创建。
