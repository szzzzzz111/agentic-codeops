# 当前 Review 清单

Active OpenSpec change：none。repair-documentation-information-architecture 已归档；semantic subject 已冻结。
后续只允许 implementation review-set.json 与 delivery-binding.json 两个 evidence tail。

Risk：high；documentation information architecture + authority-sensitive review-gate 窄修。
Repo-local receipts 只证明 mechanical consistency；用户 authority、host dispatch、archive、merge 和 push
分别由外部事实对账。

## Freeze And Scope

- [x] Planning base、authorized old remote tip 均为
  1d6f45f734124d009fa72cc54cbb080c5caa6c44，target 为 origin/main。
- [x] Epoch 7 绑定 exact scope、high risk、plan/implementation 各 2 slots 与 push ceiling。
- [x] Non-goals 排除 app/**、runtime/public contract、依赖、权限、持久化、网络默认值和原脏 worktree。
- [x] Plan 两槽绑定同一最终 plan packet，finding 已闭合，validator mechanical PASS。

## Implementation And Verification

- [x] 文档职责、当前架构入口、durable progress、OpenSpec indexes 与 Purpose 偏差已修。
- [x] Authority gate 保持 positive-slot 约束，并对 low-risk bound zero、mixed-phase zero、未来 implement
  plan binding 和 malformed counts fail closed。
- [x] HANDOFF scanner 覆盖中英文裸标签、半/全角冒号、Markdown list/emphasis/inline-code 与稳定
  live-query guidance；focused 正反例 36 passed。
- [x] Canonical verification 1052 passed；Ruff、stage-doc、skill-eval 全绿。
- [x] OpenSpec strict 25/25、JSON/AST、manifest/inventory 与 git diff --check 通过。
- [x] Final scanner remediation 已进入 verified semantic subject；post-archive review 仍由各 slot 独立给出结论。

## Archive And Delivery

- [x] Archive authority preflight PASS；OpenSpec change 已同步当前 spec 并归档到
  2026-08-31-repair-documentation-information-architecture。
- [ ] 两个既有 implementation slots refresh 同一 final post-archive packet，P0/P1/P2 清零。
- [ ] Final review-set 与 delivery-binding mechanical PASS；staged index 与 reviewed packet 精确一致。
- [ ] 创建单一 candidate，controller-only fast-forward main。
- [ ] 使用 explicit refspec + exact-old-OID lease push，并从同 endpoint 查询 remote parity。
