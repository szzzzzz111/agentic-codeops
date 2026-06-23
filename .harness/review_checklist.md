# 当前 Review 清单

当前无 active OpenSpec change。最近完成的归档：
`2026-06-23-add-live-model-provider-eval`。

## Final Stage Evidence

- Gate marker: `formal_review_evidence_gate`
- Policy marker: `continuous_authorization_does_not_replace_formal_review`
- Timing marker: `formal_review_after_final_runtime_tests`
- [x] Evaluator implementation、TDD、internal review、independent adversarial review 与 Stage Debt Sweep 完成。
- [x] Final live run 在 clean evaluator commit 上完成 10 cases / 8 calls。
- [x] Tracked evidence 为 evaluated-failure record，不是 PASS attestation。
- [x] `deepseek-v4-flash` 明确记录为未通过本 profile/rubric 的 conformance gate。
- [x] Change 已归档并同步长期 spec；merge 后 full verify 为 391 passed、1 skipped。
- [x] OpenSpec 19/19、stage closeout、ruff、stage docs 与 skill checks 通过。
- [x] `manual_stage_debt_sweep_completed`。
- [x] `formal_review_findings_closed`。
- [x] `future_stage_only`：未创建 V24。

## Next Stage

下一阶段开始时重新建立 scope、risk、allowed files、review checklist 和 OpenSpec artifacts。
