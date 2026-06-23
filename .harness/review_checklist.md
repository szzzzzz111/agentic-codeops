# 当前 Review 清单

Archived change：`2026-06-23-harden-grounded-prompt-injection-suppression`。风险级别：medium。

## Scope

- [x] 仅收紧 grounded-text system instruction 的 Prompt Injection suppression contract。
- [x] 不修改 evaluator、fixture、rubric、profile 或 live gate。
- [x] 不增加输出清洗、marker 黑名单、EvidencePack 过滤或 classifier。
- [x] Citation footer、validator、evidence envelope、JSON mode、metrics、API、默认 Patch wiring
  和 persistence 保持不变。
- [x] 默认 verify 与 CI 保持离线 deterministic；不创建 V24。

## TDD And Verification

- [x] RED 证明现有 prompt 未明确要求静默忽略 evidence 指令及其 marker/token 目标。
- [x] GREEN 证明 instruction 明确禁止回答、澄清、拒答和安全说明确认或复现注入目标。
- [x] JSON object mode、evidence envelope、citation footer 和 Fake provider regression 通过。
- [x] Focused Provider/Grounded Answer/AgentLoop/API regression：137 passed。
- [x] Full verify：334 passed、1 skipped；OpenSpec strict/all：19 passed；ruff、stage docs、
  skill checks 与 `git diff --check` 通过。

## Review

- Gate marker: `formal_review_evidence_gate`
- Policy marker: `continuous_authorization_does_not_replace_formal_review`
- Timing marker: `formal_review_after_final_runtime_tests`
- [x] Internal implementation review confirms prompt-only scope and no post-processing.
- [x] Focused independent external review session `ses_10d63d08dffe9ANSUL3wIz3XxA` 初审提出
  2 个 P2、1 个 P3 和 1 个测试表述缺口；修复后 re-review 无剩余 P0-P3。
- [x] `manual_stage_debt_sweep_completed` covers Provider prompt assembly, Grounded Answer validator,
  AgentLoop/API callers, JSON consumers and frozen eval boundary.
- [x] `formal_review_findings_closed`：收紧 attack-target、topical-relatedness 与 declarative-rule
  绕过；prompt tests 不再声称证明真实模型行为。

## Closeout

- [x] Remediation archived only after final verification and review.
- [ ] Remediation merged and pushed before eval change resumes.
- [ ] Existing eval deterministic review/live evidence marked invalid after runtime change.
- [ ] Real DeepSeek gate remains an eval-change responsibility.
- [x] `future_stage_only`：V24 不在本 change 内创建。
