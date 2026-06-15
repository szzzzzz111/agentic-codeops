# 当前 Review 清单

当前无 active development stage。V23 已合并，但 merge 后正式 review 发现未关闭 findings，
当前 closeout 已恢复为阻断状态。

## 正式 Review 证据门

- Gate marker: `formal_review_evidence_gate`
- Policy marker: `continuous_authorization_does_not_replace_formal_review`
- Timing marker: `formal_review_after_final_runtime_tests`
- [x] 连续执行授权不替代正式 review、Stage Debt Sweep、验证或 closeout gate。
- [x] 正式 code review 必须在最终 runtime/tests 变更之后执行，并明确报告 findings 或无 findings。
- [ ] `formal_review_findings_closed`：V23 merge 后正式 code review findings 已全部修复、复核并关闭。
- [ ] `P1_registry_path_mismatch`：registry path mismatch 不再被误判为 `both_missing` 并终态化。
- [ ] `P1_damaged_sqlite_metadata`：损坏 SQLite metadata 能 fail closed、返回安全结果并尝试写入 attempt audit。
- [ ] `P2_invalid_utf8_metadata`：Git metadata 非法 UTF-8 严格 fail closed。

## V23 Closeout Gate

- [x] V23 OpenSpec tasks 全部完成，用户已确认 commit/archive/merge。
- [x] Exact confirmed disposal/reconciliation、scope、ownership、HEAD/base 与 lifecycle gates 已实现。
- [x] Shared Git metadata runner timeout / pre-read hard limit 已覆盖 V21/V22/V23 metadata read。
- [x] Disposal/reconciliation strict order、idempotency、partial failure 与 scoped patch closeout 已验证。
- [x] Persistent audit、脱敏、稳定 `/chat` contract 与零越界工具调用已验证。
- [x] Targeted/adjacent regressions、full verify、OpenSpec validation 与 `git diff --check` 通过。
- [ ] `final_review_closed`：Stage Debt Sweep 与正式 final review 已在最终变更后完成，且所有有效 findings 已关闭。
- [x] V23 已归档到 `openspec/changes/archive/2026-06-15-v23-worktree-disposal-reconciliation/`。
- [ ] `review_remediation_closed`：Merge 后 review remediation、stage closeout、full verify 与 durable docs 已完成。

## 下一阶段 Gate

- [ ] V23 review findings 已关闭并通过 re-review。
- [ ] 开始下一阶段前创建 OpenSpec change。
- [ ] 开始下一阶段前同步 `.harness/allowed_files.md` 与本清单。
