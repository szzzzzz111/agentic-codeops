# 当前 Review 清单

Archived change：`2026-06-23-harden-grounded-evidence-framing`。风险级别：medium。

## Scope

- [x] Grounded user prompt 与 system allowed list 使用相同裸 citation label。
- [x] Grounded evidence 使用明确的不可信 JSON data envelope。
- [x] Instruction 禁止执行或复述 evidence 内改变回答行为、泄露内容或输出 marker 的指令。
- [x] JSON mode、validator、metrics、API、Patch wiring 和 persistence 不变。
- [x] 不修改 paused live evaluator，不创建 V24。

## TDD And Verification

- [x] RED/GREEN covers citation framing, evidence envelope, injection instruction and JSON-mode parity.
- [x] Focused Provider/Grounded Answer/AgentLoop/API regression：137 passed。
- [x] Final full verify：334 passed、1 skipped；OpenSpec strict/all：19 passed；ruff、stage docs、
  skill checks 与 `git diff --check` 通过。

## Review

- Gate marker: `formal_review_evidence_gate`
- Policy marker: `continuous_authorization_does_not_replace_formal_review`
- Timing marker: `formal_review_after_final_runtime_tests`
- [x] Internal plan and implementation review complete：确认 grounded-only mode branch、JSON
  escaping、裸 citation labels、structured-output parity 与 audit boundary。
- [x] Focused external review session `ses_10dea04ebffe0m3qVh8yY6dUs9` complete：初审无
  P0-P2、3 个 P3；移除 allowed-list bullet、收紧行为指令措辞并增加特殊字符 round-trip 后，
  re-review 确认所有 P3 关闭。
- [x] `manual_stage_debt_sweep_completed`：检查 Provider/tests、Grounded Answer
  regex/fallback、Planner/Patch JSON callers、AgentLoop/API、audit/persistence、OpenSpec/Harness
  与 paused eval；无新增阻断债务。
- [x] `formal_review_findings_closed`：无 P0/P1/P2/P3；extensionless citation 为既有 scope 外
  residual，真实模型抗注入效果由恢复后的 live gate 验证。

## Closeout

- [x] Remediation archived；merge/push 由 repository closeout workflow 完成后才能恢复 live eval。
- [x] `future_stage_only`：V24 不在本 change 内创建。
