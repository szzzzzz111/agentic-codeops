# 当前 Review 清单

Active OpenSpec change：无。

最近完成阶段：`harden-repo-mutation-locking` 已完成 implementation review、Stage Debt
Sweep、验证，并归档到
`openspec/changes/archive/2026-06-28-harden-repo-mutation-locking/`。

## 已完成阶段证据

- [x] Planning gate：proposal/design/tasks/spec delta 已创建；`.harness/allowed_files.md`
  与本 checklist 已同步；internal、Codex independent、OpenCode independent plan review
  已完成，findings 已按 `fix / clarify / reject / defer` 分类。
- [x] Implementation gate：用户明确确认后进入 runtime/tests implementation；先写 RED tests，
  再做最小 runtime 实现。
- [x] Internal implementation review：无未处理 P0/P1/P2；按 `fix` 关闭 lock acquisition
  exception、acquired/released audit outcome、exception-handler release failure 和 trace
  ordering。
- [x] Codex independent final review：发现 P1 standalone `verification_run` runner exception
  可能遗留 lock；已按 `fix` 补 safe `runner_error` result 与释放锁回归测试，复核确认
  P1 关闭且无新 P0/P1/P2。
- [x] OpenCode final implementation review：先 `opencode session list`，再复用 session
  `ses_1018bd2aeffeKLTCcQhhuQ1jFZ`；无 P0/P1/P2；P3 findings 已按
  `fix / clarify / defer` triage。
- [x] Stage Debt Sweep：覆盖 changed runtime/tests/docs/specs/Harness、直接依赖、共享状态
  和调用路径；未发现新的 blocking debt。
- [x] Focused repo mutation lock tests：`pytest tests/test_repo_mutation_locking.py -q`
  为 17 passed。
- [x] Adjacent patch/worktree/promotion/audit/AgentLoop/API regressions：focused adjacent
  group 为 227 passed。
- [x] `openspec validate --all`：archive 前 23 passed、0 failed；archive 后 22 passed、0 failed。
- [x] `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`：pytest 486 passed、1
  skipped；ruff、stage docs scan、skill eval structure scan 均通过。
- [x] `git diff --check`：通过，仅有 CRLF normalization warnings。

## 下一阶段 gate

- [ ] 新阶段开始前重新读取 `AGENTS.md` 及必读文档。
- [ ] 新阶段开始前检查 branch、worktree、recent commits、remote sync 和 active OpenSpec changes。
- [ ] 新阶段必须先同步 `.harness/allowed_files.md` 与本 checklist。
- [ ] Medium/high risk 阶段必须按流程完成 plan review、implementation review、Stage Debt
  Sweep 和 deterministic verification。
