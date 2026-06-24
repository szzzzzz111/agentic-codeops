# 当前 Review 清单

Active change：`classify-live-eval-transport-blockers`。风险级别：high。

## Scope

- [x] 仅修改 live evaluator 的 transport/sandbox/provider-contact blocker 分类与脱敏诊断。
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
- [x] 用户确认后进入 TDD implementation。

## Implementation / Verification

- Gate marker：`formal_review_evidence_gate`
- Policy marker：`continuous_authorization_does_not_replace_formal_review`
- Timing marker：`formal_review_after_final_runtime_tests`
- [x] RED tests cover redacted transport metadata, all-unavailable blocker, partial-contact blocker, full-contact conformance FAIL, live shell guard, builder-level provider-contact guard, diagnostic code sanitization and no tracked evidence.
- [x] Focused evaluator tests passed：`pytest tests/test_live_model_provider_eval.py -q` → `64 passed in 1.28s`。
- [x] Full deterministic verify passed：`powershell -ExecutionPolicy Bypass -File scripts/verify.ps1` → `398 passed, 1 skipped`; ruff passed; stage docs scan passed; skill eval structure scan passed。
- [x] OpenSpec / docs / diff checks passed after final runtime/test change：
  - `openspec validate classify-live-eval-transport-blockers --strict` → valid
  - `openspec validate --all` → 21 passed, 0 failed
  - `powershell -ExecutionPolicy Bypass -File scripts/check_stage_docs.ps1` → valid
  - `git diff --check` → clean except existing CRLF normalization warnings
- [x] Internal review covers evidence lifecycle, redaction, shell guard and historical evidence immutability.
  - Finding fixed：`build_evaluated_failure_record()` now rejects reports where any required provider case lacks evaluable provider contact.
  - Finding fixed：transport diagnostic `error_class` is reduced to a safe code token before serialization.
- [x] Independent adversarial review completed with no P0/P1 findings.
  - P2.1 triage：grounded diagnostics concern rejected/covered; `GroundedAnswerGenerator` already preserves allowlisted `error_class`, and regression test now confirms unavailable grounded case reports redacted diagnostics.
  - P2.2 triage：`api_subprocess_error` / `run_timeout` remain existing integrity-failure paths with no tracked evidence; not reclassified as transport blocker in this change.
- [x] `manual_stage_debt_sweep_completed`：inspected changed evaluator paths, `scripts/run_live_model_eval.ps1`, `app/providers/model_provider.py`, and `app/answering/grounded_answer.py`.
  - No `app/**` runtime changes.
  - Provider `error_class` source is class-name based; evaluator sanitizer still fails closed for malformed values.
  - `system_fingerprint` remains redacted to status, and attestation/failure record allowlists remain narrow.
  - Local report / attestation / evaluated-failure writers still use exclusive-create semantics.
- [x] `formal_review_findings_closed`。
- [ ] Archive/merge/push only after deterministic verification, formal review and OpenSpec archive sync pass.
- [x] `future_stage_only`：V24 不在本 change 内创建。
