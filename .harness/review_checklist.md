# 当前 Review 清单

当前无 active development stage。V23 merge 后正式 review findings 已修复并完成 re-review，
remediation closeout 与最终独立 Stage Debt Sweep 已完成。

## 正式 Review 证据门

- Gate marker: `formal_review_evidence_gate`
- Policy marker: `continuous_authorization_does_not_replace_formal_review`
- Timing marker: `formal_review_after_final_runtime_tests`
- Manual judgment marker: `manual_judgment_gates_completed`
- [x] 连续执行授权不替代正式 review、Stage Debt Sweep、验证或 closeout gate。
- [x] 正式 code review 必须在最终 runtime/tests 变更之后执行，并明确报告 findings 或无 findings。
- [x] `manual_stage_debt_sweep_completed`：人工复核 changed runtime 与 adjacent older paths；
  脚本仅覆盖机械可搜索项，脚本通过不替代人工代码/测试债审查。
- [x] `formal_review_findings_closed`：V23 merge 后正式 code review findings 已全部修复、复核并关闭。
- [x] `P1_registry_path_mismatch`：registry path mismatch 不再被误判为 `both_missing` 并终态化。
- [x] `P1_damaged_sqlite_metadata`：损坏 SQLite metadata 能 fail closed、返回安全结果并尝试写入 attempt audit。
- [x] `P2_invalid_utf8_metadata`：Git metadata 非法 UTF-8 严格 fail closed。

## V23 Closeout Gate

- [x] V23 OpenSpec tasks 全部完成，用户已确认 commit/archive/merge。
- [x] Exact confirmed disposal/reconciliation、scope、ownership、HEAD/base 与 lifecycle gates 已实现。
- [x] Shared Git metadata runner timeout / pre-read hard limit 已覆盖 V21/V22/V23 metadata read。
- [x] Disposal/reconciliation strict order、idempotency、partial failure 与 scoped patch closeout 已验证。
- [x] Persistent audit、脱敏、稳定 `/chat` contract 与零越界工具调用已验证。
- [x] Targeted/adjacent regressions、full verify、OpenSpec validation 与 `git diff --check` 通过。
- [x] `final_review_closed`：Stage Debt Sweep 与正式 final review 已在最终变更后完成，且所有有效 findings 已关闭。
- [x] V23 已归档到 `openspec/changes/archive/2026-06-15-v23-worktree-disposal-reconciliation/`。
- [x] `review_remediation_closed`：Merge 后 review remediation、stage closeout、full verify 与 durable docs 已完成。
- [x] 最终独立 review 无新增 P0/P1/P2；V21 inspection 流式 Git 子进程与 V20 create/rollback
  Git 子进程硬化债已记录到 durable docs，留待独立阶段处理。

## Manual Judgment Gates

- [x] Stage intent / scope：V23 保持 disposal/reconciliation 边界，未扩入 promotion 或隐式修复。
- [x] Safety / architecture：scope、ownership、fail-closed、固定工具链与脱敏边界经正式 review 复核。
- [x] Test adequacy：requirements、non-goals、错误路径、安全边界与相邻回归均有验证证据。
- [x] Review triage：内部与外部 findings 已逐项核实、分类、修复或拒绝，并完成 re-review。
- [x] Semantic parity：durable docs、Harness、长期 specs 与当前无 active stage 状态一致。
- [x] Archive / merge / handoff truth：V23 archive、main 历史、feature branch retention 与 handoff
  表述已对照真实 Git 状态复核。
- [x] 脚本只检查人工判断门证据 marker；上述语义结论由人工 review 承担。

## 下一阶段 Gate

- [x] V23 review findings 已关闭并通过 re-review。
- [ ] 开始下一阶段前创建 OpenSpec change。
- [ ] 开始下一阶段前同步 `.harness/allowed_files.md` 与本清单。
