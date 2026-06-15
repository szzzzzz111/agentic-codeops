# 当前 Review 清单

当前无 active development stage。V23 Worktree Disposal / Reconciliation 已实现、review 并归档。

## V23 Closeout Gate

- [x] V23 OpenSpec tasks 全部完成，用户已确认 commit/archive/merge。
- [x] Exact confirmed disposal/reconciliation、scope、ownership、HEAD/base 与 lifecycle gates 已实现。
- [x] Shared Git metadata runner timeout / pre-read hard limit 已覆盖 V21/V22/V23 metadata read。
- [x] Disposal/reconciliation strict order、idempotency、partial failure 与 scoped patch closeout 已验证。
- [x] Persistent audit、脱敏、稳定 `/chat` contract 与零越界工具调用已验证。
- [x] Targeted/adjacent regressions、full verify、OpenSpec validation 与 `git diff --check` 通过。
- [x] Stage Debt Sweep 与 internal final review 已完成并修复有效 findings。
- [x] V23 已归档到 `openspec/changes/archive/2026-06-15-v23-worktree-disposal-reconciliation/`。
- [ ] Archive 后 stage closeout、full verify 与 merge 后 durable docs 已完成。

## 下一阶段 Gate

- [ ] 开始下一阶段前创建 OpenSpec change。
- [ ] 开始下一阶段前同步 `.harness/allowed_files.md` 与本清单。
