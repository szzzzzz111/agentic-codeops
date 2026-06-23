# 当前 Review 清单

Active change：`harden-grounded-prompt-injection-suppression`。风险级别：medium。

## Scope

- [x] 仅收紧 grounded-text system instruction 的 Prompt Injection suppression contract。
- [x] 不修改 evaluator、fixture、rubric、profile 或 live gate。
- [x] 不增加输出清洗、marker 黑名单、EvidencePack 过滤或 classifier。
- [x] Citation footer、validator、evidence envelope、JSON mode、metrics、API、默认 Patch wiring
  和 persistence 保持不变。
- [x] 默认 verify 与 CI 保持离线 deterministic；不创建 V24。

## TDD And Verification

- [ ] RED 证明现有 prompt 未明确要求静默忽略 evidence 指令及其 marker/token 目标。
- [ ] GREEN 证明 instruction 明确禁止回答、澄清、拒答和安全说明确认或复现攻击目标。
- [ ] JSON object mode、evidence envelope、citation footer 和 Fake provider regression 通过。
- [ ] Focused Provider/Grounded Answer/AgentLoop/API regression 通过。
- [ ] Full verify、OpenSpec strict/all、ruff、stage docs、skill checks 与 `git diff --check` 通过。

## Review

- Gate marker: `formal_review_evidence_gate`
- Policy marker: `continuous_authorization_does_not_replace_formal_review`
- Timing marker: `formal_review_after_final_runtime_tests`
- [ ] Internal implementation review confirms prompt-only scope and no post-processing.
- [ ] Focused independent external review seeks bypasses, instruction ambiguity and contract drift.
- [ ] `manual_stage_debt_sweep_completed` covers Provider prompt assembly, Grounded Answer validator,
  AgentLoop/API callers, JSON consumers and frozen eval boundary.
- [ ] `formal_review_findings_closed`。

## Closeout

- [ ] Remediation archived only after final verification and review.
- [ ] Remediation merged and pushed before eval change resumes.
- [ ] Existing eval deterministic review/live evidence marked invalid after runtime change.
- [ ] Real DeepSeek gate remains an eval-change responsibility.
- [x] `future_stage_only`：V24 不在本 change 内创建。
