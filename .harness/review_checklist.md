# 当前 Review 清单

当前无 active development stage。V22 Worktree Re-verification 已实现、review 并归档。

## V22 Closeout Gate

- [x] V22 post-merge debt remediation 已证明 malformed Git registry output 即使夹带 expected path 仍 fail closed。
- [x] V22 post-merge debt remediation commit `454d145` 已 fast-forward 合并并推送到 `main`。
- [x] OpenSpec change tasks 全部完成且 external review 已处理。
- [x] V22 targeted tests、相关回归、full verify、OpenSpec validation 与 `git diff --check` 通过。
- [x] Stage Debt Sweep 与 internal final review 已完成并修复有效 findings。
- [x] Long-term specs 已同步，archive-sync requirement headers 已对齐。
- [x] V22 已归档到 `openspec/changes/archive/2026-06-14-v22-worktree-re-verification/`。
- [x] Archive 后 OpenSpec、stage closeout 与 full verify 通过。
- [x] Merge / push 后 durable docs 记录真实 main/remote 状态、验证证据与 branch retention 决策。

## 下一阶段 Gate

- [ ] 开始下一阶段前创建 OpenSpec change。
- [ ] 开始下一阶段前同步 `.harness/allowed_files.md` 与本清单。
