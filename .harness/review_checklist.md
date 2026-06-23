# 当前 Review 清单

Archived change：`2026-06-23-require-grounded-citation-footer`。风险级别：medium。

## Scope

- [x] 每个 grounded response 最后一行只包含一个裸 allowed citation label。
- [x] Footer contract 同样适用于回答、澄清和拒答。
- [x] 不自动追加 citation，不放宽 validator。
- [x] Evidence envelope、JSON mode、metrics、API、Patch wiring 和 persistence 不变。
- [x] 不修改 paused live evaluator，不创建 V24。

## TDD And Verification

- [x] RED/GREEN covers final-line-only bare footer and forbidden wrappers/prefixes.
- [x] Focused Provider/Grounded Answer/AgentLoop/API regression：137 passed。
- [x] Full verify：334 passed、1 skipped；OpenSpec strict/all：19 passed；ruff、stage docs、
  skill checks 与 `git diff --check` 通过。

## Review

- Gate marker: `formal_review_evidence_gate`
- Policy marker: `continuous_authorization_does_not_replace_formal_review`
- Timing marker: `formal_review_after_final_runtime_tests`
- [x] Internal plan and implementation review complete：确认 footer 仅为 instruction、无
  post-processing、JSON mode 与 validator 未改。
- [x] Focused external review complete：初审唯一 P2 为 Fake provider contract mismatch；按
  TDD 对齐 footer 后 re-review 确认无 P0-P3。
- [x] `manual_stage_debt_sweep_completed`：检查 Fake/real Provider、Grounded Answer
  validator、JSON callers、AgentLoop/API、docs/spec 与 paused eval；无新增阻断债务。
- [x] `formal_review_findings_closed`：instruction 严格于 backward-compatible validator 为有意
  设计；clarification/refusal footer 为本 remediation 明确目标。

## Closeout

- [x] Remediation archived；merge/push 由 repository closeout workflow 完成后才能恢复 live eval。
- [x] `future_stage_only`：V24 不在本 change 内创建。
