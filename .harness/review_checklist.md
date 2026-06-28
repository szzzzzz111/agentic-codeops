# 当前 Review 清单

Active OpenSpec change：无。

最近归档 OpenSpec change：`harden-worktree-inspection-timeouts`。

风险级别：high。目标是修复 `app/worktrees/inspection.py` read-only inspection streaming
Git diff / preview 无 timeout wait 的代码债；该阶段已归档。

## Planning / Harness

- [x] 已读取 `AGENTS.md` 及必读文档、OpenSpec README、Harness rules、workflow/review skills。
- [x] 已检查 branch、worktree、recent commits、remote sync 和 active OpenSpec changes。
- [x] 已选择代码债：`app/worktrees/inspection.py` streaming hunk count / preview timeout hardening。
- [x] 已创建 OpenSpec proposal、design、tasks、spec delta。
- [x] 已同步 `.harness/allowed_files.md` 与本 checklist。

## Plan Review Gate

- [x] Internal plan review：proposal/design/tasks/spec delta/test plan/Harness 边界；发现 wait-only timeout 不覆盖 blocked stdout read，已按 `fix` 修正为覆盖 read + wait 的总 deadline。
- [x] Codex independent plan review：subagent `Euler` 完成只读 review；No P0/P1/P2 findings。P3 residual risks 为 Windows pipe blocked read、kill/reap、partial stdout 不误报完整结果、helper 状态区分和 RED tests 覆盖 blocked read；已体现在 design/tasks 中。
- [x] OpenCode independent plan review：已先 `opencode session list`，并复用 session `ses_1018bd2aeffeKLTCcQhhuQ1jFZ`；结论无 P0/P1/P2，三个 P3 均按 `clarify` 处理。
- [x] 所有 plan findings 按 `fix / clarify / reject / defer` 分类并处理：internal finding 按 `fix`；OpenCode P3 findings 按 `clarify`；Codex P3 residual risks 已纳入 implementation guardrails。
- [x] `openspec validate harden-worktree-inspection-timeouts --strict`：通过。
- [x] 停在 implementation confirmation gate，用户已明确确认进入 implementation。

## Implementation Gate（用户确认后）

- [x] RED tests：hunk count streaming timeout kills/reaps process and returns partial；初次 focused run 预期失败，当前已通过。
- [x] RED tests：preview streaming timeout omits affected file, marks partial, and does not expose raw path/exception/diff；初次 focused run 预期失败，当前已通过。
- [x] Runtime：`inspection.py` 增加 timeout-bounded streaming Git process handling，覆盖 stdout consumption 与 process finalization。
- [x] Preserve：fixed argv、`shell=False`、`GIT_OPTIONAL_LOCKS=0`、preview bounds/redaction、untracked count-only、metadata runner behavior；focused inspection tests 20 passed。

## Final Review / Verification（implementation 后）

- [x] Focused `pytest tests/test_worktree_inspection.py -q`：20 passed。
- [x] Adjacent worktree/AgentLoop/API regressions：183 passed。
- [x] `openspec validate --all`：23 passed，0 failed。
- [x] `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`：pytest 489 passed、1 skipped；ruff、stage docs scan、skill eval structure scan 均通过。
- [x] `git diff --check`：通过，仅有 CRLF normalization warnings。
- [x] Final implementation review and finding triage：internal review 无 P0/P1/P2；OpenCode final review 复用 session `ses_1018bd2aeffeKLTCcQhhuQ1jFZ`，发现 P2 unrealistic read-timeout test，按 `fix` 改为 watchdog timer path 测试；P3 docstring / dead code 已处理；focused OpenCode re-review 确认 P2 closed 且 no new P0/P1/P2。
- [x] Focused Stage Debt Sweep：覆盖 `app/worktrees/inspection.py`、`tests/test_worktree_inspection.py`、Harness / OpenSpec / PROGRESS / HANDOFF、直接依赖 `app/worktrees/manager.py` inspection wrapper 与 `app/harness/kernel.py` worktree status formatting；未发现新增 blocking debt，`manager.py` create / rollback subprocess timeout 仍为既有独立债务。
- [x] Archive readiness check：blocking findings 已关闭，OpenSpec all / full verify / diff check 均通过，可归档。

## Archive / Closeout

- [x] `openspec archive harden-worktree-inspection-timeouts --yes`：成功，归档到 `openspec/changes/archive/2026-06-28-harden-worktree-inspection-timeouts/`。
- [x] Archive 后 `openspec list`：No active changes found。
- [x] Archive 后 `openspec validate --all`：22 passed，0 failed。
