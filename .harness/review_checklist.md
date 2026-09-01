# 当前 Review 清单

Active OpenSpec change：none。`add-governed-run-contract` 已归档到
`openspec/changes/archive/2026-09-01-add-governed-run-contract/`。

Risk：high / L3。新增内部 runtime contract、只读 Git subprocess collector 与人工 review 决策语义。
Authority 绑定 plan/implementation 各 2 个独立 slots；首轮 reviewer 必须空上下文、实例分离并绑定同一 packet。

## Freeze And Plan

- [x] Live `origin/main`、remote endpoints、planning base 与独立干净 worktree 已复核。
- [x] 产品边界固定为 `RunContract + GitSnapshot + AgentClaim + VerificationReceipt`。
- [x] 决策集合固定为 `continue / intervene / needs_human / ready_for_review`；所有结果均不代表任务完成。
- [x] Non-goals 排除 public API、persistence、Agent launcher、daemon、多 Agent、自动修复和 Git delivery。
- [x] Proposal、design、tasks、spec delta 与 planned RED cases 完成内部一致性复核。
- [x] 两个空上下文独立 plan-review slots 绑定同一冻结 packet，P0/P1 清零。
- [x] OpenSpec strict、plan review-set validator 与 implement authority preflight 通过。
- [x] 用户完成 L3 design/tasks/spec decision-level implementation confirmation。

## TDD And Implementation

- [x] RED 覆盖 out-of-scope path、all-untracked/ignored path、dirty baseline、repo/HEAD mismatch、缺失/歧义终态、
  zero-change claim、cross-run/thread/receipt replay、verification 缺失/失败、receipt snapshot drift 与 claim ceiling。
- [x] 实现 immutable contracts、Codex event adapter、read-only Git snapshot collector 和纯 evaluator。
- [x] `continue` 只用于未完成且无已知 drift；`intervene` 用于合同/证据冲突；`needs_human` 用于 completion
  claim 后缺失或失败的验证；`ready_for_review` 只用于同快照验证通过且 scope 合法。
- [x] Git collector 使用 child-env allowlist，在 status/diff 前拒绝 symlink/gitlink 与全部 effective repository scopes
  中的 clean/process filter，禁用 fsmonitor/ext-diff/textconv/交互，固定 argv、`shell=False`、
  `GIT_OPTIONAL_LOCKS=0`、timeout/output cap 和双稳定采样；拒绝 symlink/outside/non-repository/malformed 状态，
  仅从 code-owned default 解析 repository 外 Git executable，绑定完整 stage-0 index path/mode/object identity，
  以 no-follow raw reads 绑定全部 tracked bytes/mode，
  显式记录包括 ignored 在内的 all-untracked inventory；不支持 whole-tree containment 的平台 spawn 前 fail closed；
  不运行 Agent、不修改 index/worktree。
- [x] 保持 `/chat`、CLI、ToolRegistry、provider 默认值、现有 patch/worktree/verification 行为不变。

## Review And Verification

- [x] Focused tests 与 qualification regression 全绿。
- [x] Changed Python Ruff、`git diff --check`、OpenSpec strict 通过。
- [x] Canonical `python -I scripts/verify.py` 全绿。
- [x] Final implementation review 与 focused Stage Debt Sweep 完成，所有 P0/P1 关闭。
- [x] 最终报告明确 `code_ready`/review 状态、未知项和 claim ceiling；报告时保持未 archive、未 commit、未 merge、未 push。

## Archive And Delivery

- [x] Archive authority preflight 消费当前两席 implementation review set，随后同步长期 spec 并归档 active change。
- [x] Archive 已创建长期 `governed-run-contract` spec；durable progress/feature 与 Harness final state 已同步。
- [x] Archive 后 canonical verification `1142 passed`，full Ruff、stage-doc/skill-eval、OpenSpec all 26/26 与
  `git diff --check` 全绿；focused + qualification regression `90 passed`。
- [ ] 原 A/B reviewer 对同一 final post-archive packet 复审，P0/P1 清零并刷新两席 review-set。
- [ ] Delivery binding、精确 staged index 与 commit authority preflight 全部绑定同一 packet。
- [ ] 创建单一 candidate，ff-only 合并到 main，以 exact-old-OID lease 显式 push，并从同 endpoint 对账。
