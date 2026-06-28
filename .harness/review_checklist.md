# 当前 Review 清单

Active OpenSpec change：无。
最近归档 OpenSpec change：`harden-worktree-create-timeouts`。
风险级别：high。

目标是修复 `app/worktrees/manager.py` worktree create / workspace preflight /
rollback Git subprocess 没有 timeout 与输出硬上限的代码债。

## Planning / Harness

- [x] 已读取 `AGENTS.md`、必读文档、OpenSpec README、Harness rules、workflow/review skills。
- [x] 已检查 branch、worktree、recent commits、remote sync 和 active OpenSpec changes。
- [x] 已选择代码债: `app/worktrees/manager.py` worktree create / rollback subprocess timeout hardening。
- [x] 已创建 OpenSpec proposal、design、tasks、spec delta。
- [x] 已同步 `.harness/allowed_files.md` 与本 checklist。

## Plan Review Gate

- [x] Internal plan review: 发现 `git check-ignore` 非零退出是业务语义，不能与 timeout/oversize 混为 hard failure；已按 `fix` 写入 design/tasks。
- [x] Codex independent plan review: subagent `Dewey` 完成只读 review；No P0/P1；2 个 P2 均按 `fix` 修正。
- [x] OpenCode independent plan review: 已先 `opencode session list`，并复用 session `ses_1018bd2aeffeKLTCcQhhuQ1jFZ`；No P0/P1/P2；P3 findings 已分类处理。
- [x] 所有 plan findings 已按 `fix / clarify / reject / defer` 分类并处理。
- [x] `openspec validate harden-worktree-create-timeouts --strict` 通过。
- [x] 已停在 implementation confirmation gate，用户已批准进入 implementation。

## Implementation Gate

- [x] RED tests: worktree create / preflight Git subprocess timeout returns safe failure without raw output。
- [x] RED tests: stdout/stderr oversize kills/reaps process and returns safe failure。
- [x] RED tests: rollback unlock/remove timeout or subprocess failure remains best-effort and does not hang。
- [x] Runtime: `manager.py` 增加 bounded Git subprocess helper，覆盖 timeout、output cap、kill/reap、fixed argv、`shell=False`、`GIT_OPTIONAL_LOCKS=0`。
- [x] Preserve: existing create reasons、dirty workspace semantics、ignored file allowance、detached locked worktree layout、rollback cleanup、state transitions 和 no local path exposure。
- [x] Watch: `_is_repopilot_ignored()` / `git check-ignore` 也通过 bounded helper 获得 `GIT_OPTIONAL_LOCKS=0`，且非零业务退出仍保留为 `repopilot_not_ignored`。

## Final Review / Verification

- [x] Focused `pytest tests/test_worktree_isolation.py -q`。
- [x] Adjacent worktree/AgentLoop/API regressions。
- [x] `openspec validate --all`。
- [x] `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`。
- [x] `git diff --check`。
- [x] Final implementation review and finding triage: internal review no P0/P1/P2；OpenCode final review 复用 session `ses_1018bd2aeffeKLTCcQhhuQ1jFZ`，no P0/P1/P2。P3-1 `_is_bare_repo()` try/except 建议按 `reject/clarify` 处理，当前传播 subprocess failure 到 `create_failed` 是 fail-closed；P3-2 oversize extra-byte detection 按 `clarify` 补充注释。
- [x] Focused Stage Debt Sweep: 覆盖 changed runtime/tests/docs/OpenSpec/Harness、`app/harness/kernel.py`、`app/tools/tool_executor.py` 和 `app/worktrees/*` subprocess 调用；未发现 blocking debt。相邻剩余债: `app/worktrees/disposal.py` 和 `app/worktrees/git_metadata.py` 的 subprocess hardening 另开阶段；本地 `__pycache__` 未被 Git 跟踪。
- [x] Archive readiness check: blocking findings closed; `openspec validate --all`, full `scripts/verify.ps1`, focused tests, ruff, and `git diff --check` passed before archive.

## Archive / Closeout

- [x] `openspec archive harden-worktree-create-timeouts --yes` 成功，归档到 `openspec/changes/archive/2026-06-28-harden-worktree-create-timeouts/`。
- [x] Archive 后 `openspec list`: No active changes found。
- [x] Archive 后 `openspec validate --all`: 22 passed，0 failed。
