# 当前 Review 清单

Active change：`add-live-model-provider-eval`。风险级别：high。

## Reshaped Scope

- [x] Prompt Injection 与其他 conformance gates 保持 hard gate；FAIL 仍返回 1。
- [x] PASS-only attestation contract 保持不变。
- [ ] Evaluated-failure record 使用固定 allowlist schema 和独立 failures 目录。
- [ ] Change archive 明确只表示 evaluator readiness，不表示 provider certification。
- [x] Runtime、fixture、rubric、profile、默认 CI 和 V24 不在 reshape scope。

## TDD And Verification

- [x] RED/GREEN covers exact failure schema, forbidden fields, deterministic ordering and UTC time.
- [x] RED/GREEN distinguishes trustworthy conformance FAIL from SKIP and evaluation integrity failure; all single-case and whole-run call-count gates are integrity blockers.
- [x] Simulated PASS still writes only attestation; trustworthy FAIL writes only failure record and exits 1.
- [x] Integrity failure writes no tracked evidence and remains non-archivable.
- [x] Focused evaluator tests：57 passed；adjacent regression：167 passed；full verify：391 passed、1 skipped；ruff、OpenSpec strict/all 与 `git diff --check` 通过。

## Review

- Gate marker: `formal_review_evidence_gate`
- Policy marker: `continuous_authorization_does_not_replace_formal_review`
- Timing marker: `formal_review_after_final_runtime_tests`
- [x] Internal review verifies archive semantics do not weaken any hard gate.
- [x] Independent adversarial review session `ses_10c530656ffegAJ98pMZlih0iI` checked misclassification, incomplete reports, false certification, schema leakage, timeout and exit codes.
- [x] Evidence writers use exclusive create; PASS/FAIL tracked evidence is mutually exclusive.
- [x] `manual_stage_debt_sweep_completed` covers report/attestation/failure writers, runner state classification,
  CLI output, docs and frozen runtime boundary.
- [x] `formal_review_findings_closed`：message-string P1 replaced by `EvaluationIntegrityError`; incomplete 10-case/8-call reports, invalid SHA/UTC and deadline integrity paths fail closed. Existing unused serialization round-trip/version suggestions remain out of scope and non-blocking.

## Closeout

- [x] Historical live FAIL reports remain local sanitized evidence and are not retroactive tracked records.
- [ ] Final evaluator implementation committed before live execution.
- [ ] Final live run produces either PASS attestation or trustworthy evaluated-failure record.
- [ ] Final evidence review verifies evaluator commit、UTC time、provider/model、rubric、failed gates and report hash.
- [ ] SKIP or evaluation integrity failure cannot satisfy archive conditions.
- [ ] Change archived docs explicitly distinguish evaluator readiness from provider conformance.
- [x] `future_stage_only`：V24 不在本 change 内创建。
