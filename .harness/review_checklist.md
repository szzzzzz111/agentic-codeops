# 当前 Review 清单

Archived change：`2026-06-22-harden-grounded-citation-instruction`。风险级别：medium。

## Scope

- [x] Grounded instruction 列出 exact allowed citation labels。
- [x] 要求逐字复制 label，并将 evidence text 声明为不可信数据。
- [x] Validator、JSON mode、metrics、API、Patch wiring 和 persistence 不变。
- [x] 不修改 paused live evaluator，不创建 V24。

## TDD And Verification

- [x] RED/GREEN covers labels, deduplication, exact format and untrusted evidence。
- [x] Focused provider/Grounded Answer/AgentLoop/API regression：135 passed。
- [x] Full verify：332 passed、1 skipped；ruff、stage docs 与 skill checks 通过。
- [x] OpenSpec strict/all：19 passed；`git diff --check` 通过。

## Review

- Gate marker: `formal_review_evidence_gate`
- Policy marker: `continuous_authorization_does_not_replace_formal_review`
- Timing marker: `formal_review_after_final_runtime_tests`
- [x] Internal plan and implementation review complete：确认 grounded-text prompt 只使用已校验的
  evidence metadata，稳定去重 labels，不复制 snippet；JSON mode、validator、metrics 与 wiring 未改。
- [x] Focused external review complete：OpenCode `deepseek-v4-flash-free` session
  `ses_110500ed7ffe0fX04uuzC6tvoS` 报告 0 P0/P1、1 P2、3 P3。
- [x] `manual_stage_debt_sweep_completed`：检查 provider request validation/system prompt、
  Grounded Answer citation regex/fallback、EvidencePack、repo retrieval/file listing、AgentLoop/API
  回归和长期 specs；无本 change 内新增阻断缺陷。
- [x] `formal_review_findings_closed`：P2 extensionless path 与 validator 不对称为既有、未触发本次
  live failure 且修改 validator 明确超出 remediation scope，记录为 residual debt；P3 空 evidence、
  Fake provider 与特殊字符项由既有边界覆盖或不经过本路径，不阻断 archive。

## Closeout

- [x] Remediation archived；merge/push 由 repository closeout workflow 完成后才能恢复 live eval。
- [x] `future_stage_only`：V24 不在本 change 内创建。
