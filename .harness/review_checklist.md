# 当前 Review 清单

Active OpenSpec change：无。

最近完成阶段：V25 `add-verified-patch-promotion` 已完成 implementation review、Stage Debt Sweep、验证，并归档到
`openspec/changes/archive/2026-06-27-add-verified-patch-promotion/`。

## 当前状态

- [x] `openspec list`：No active changes found。
- [x] V25 OpenSpec archive 后 `openspec validate --all`：21 passed，0 failed。
- [x] V25 final full verify：`scripts/verify.ps1` 通过，pytest 469 passed、1 skipped；ruff、stage docs scan、skill eval structure scan passed。
- [x] V25 final review：internal、Codex independent、OpenCode independent findings 已按 `fix / clarify / reject / defer` triage；无剩余 P0/P1/P2。
- [x] V25 Stage Debt Sweep：已覆盖 changed runtime/tests/docs/specs/Harness；残余 P3 为无全局 repo lock 下的极窄跨进程 HEAD/file mutation race，记录为后续 hardening。

## 下一阶段 gate

- [ ] 新阶段开始前重新读取 `AGENTS.md` 及必读文档。
- [ ] 新阶段开始前检查 branch、worktree、recent commits、remote sync 和 active OpenSpec changes。
- [ ] 新阶段必须先同步 `.harness/allowed_files.md` 与本 checklist。
- [ ] Medium/high risk 阶段必须按流程完成 plan review、implementation review、Stage Debt Sweep 和 deterministic verification。
