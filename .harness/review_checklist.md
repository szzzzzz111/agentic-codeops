# 当前 Review 清单

Active OpenSpec change：无。

最近完成阶段：`update-repo-stage-workflow-skill` 已完成 low-risk workflow/process 文档更新，
并归档到 `openspec/changes/archive/2026-06-28-update-repo-stage-workflow-skill/`。

## 已完成阶段证据

- [x] Planning / Harness：已读取入口文档；已检查 branch、worktree、recent commits、remote
  sync 和 active OpenSpec；已创建 proposal、tasks、spec delta；已同步 allowed files 与本 checklist。
- [x] Implementation：`repo-stage-workflow` 明确 OpenSpec 负责规格基线，Superpowers-style
  execution discipline 负责读规格、隔离、TDD、验证、review、finish 和 skill 自检；需求变化或设计矛盾先回 OpenSpec。
- [x] Current-state drift：`docs/PROGRESS.md` 与 `HANDOFF_TO_NEXT_CHAT.md` 不再要求完成已完成的
  repo mutation locking closeout；`tests/test_chat_api.py` docs consistency assertion 不再要求 active OpenSpec 必须为无。
- [x] Internal review：scope、roadmap truth、process-only boundary、skill clarity、文档所有权；无未处理 P0/P1/P2。测试契约问题已按 `fix` 处理。
- [x] Stage Debt Sweep：changed workflow skill、Harness、PROGRESS/HANDOFF current-state sections、
  `tests/test_chat_api.py` docs consistency assertion；无新增 blocking debt。
- [x] `openspec validate update-repo-stage-workflow-skill --strict`：通过。
- [x] `openspec validate --all`：archive 前 23 passed、0 failed；archive 后 22 passed、0 failed。
- [x] `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`：pytest 486 passed、1 skipped；ruff、stage docs scan、skill eval structure scan 均通过。
- [x] `git diff --check`：通过，仅有 CRLF normalization warnings。
- [x] Archive 后 `openspec list`：No active changes found。

## 下一阶段 gate

- [ ] 新阶段开始前重新读取 `AGENTS.md` 及必读文档。
- [ ] 新阶段开始前检查 branch、worktree、recent commits、remote sync 和 active OpenSpec changes。
- [ ] 新阶段必须先同步 `.harness/allowed_files.md` 与本 checklist。
- [ ] Medium/high risk 阶段必须按流程完成 plan review、implementation review、Stage Debt
  Sweep 和 deterministic verification。
