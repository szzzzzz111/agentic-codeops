# 交接给下一轮 Chat

## 当前基线

- 当前分支: `codex/harden-worktree-create-timeouts`。
- Active OpenSpec change：无。
- 最近归档 OpenSpec change：`harden-worktree-create-timeouts`，归档到 `openspec/changes/archive/2026-06-28-harden-worktree-create-timeouts/`。
- 风险级别: high。
- 本阶段目标: 修复 worktree create / workspace preflight / rollback Git subprocess 没有 timeout 与输出硬上限的代码债。
- Scope 仍然只限 `app/worktrees/manager.py`、`tests/test_worktree_isolation.py`、本 change 的 OpenSpec/Harness 文档和真实状态文档。
- 本阶段不修改 `/chat` public contract、provider runtime、live eval、默认 CI、网络依赖、后台任务、runtime subagent、connector、notification、commit/merge/push automation、branch/PR automation 或 `git worktree prune`。

继续前先刷新 live state:

```powershell
git status --short --branch
git log -5 --oneline --decorate
openspec list
openspec validate --all
```

## 已完成内容

- OpenSpec planning 已完成，并经过 internal、Codex independent、OpenCode independent plan review。
- Plan findings 已按 `fix / clarify / reject / defer` 分类处理。
- 已实现 manager-local bounded Git helper:
  - fixed argv + `shell=False`
  - `GIT_OPTIONAL_LOCKS=0`
  - `WORKTREE_GIT_TIMEOUT_SECONDS = 10.0`
  - `WORKTREE_GIT_OUTPUT_MAX_BYTES = 256_000`
  - Windows-safe stdout/stderr capped reader threads
  - timeout / oversize / read failure 会 kill/reap 并 fail-closed
- `_is_repopilot_ignored()` 已改为复用 bounded helper，并明确区分:
  - return code 0: ignored
  - return code 1: not ignored -> existing `repopilot_not_ignored`
  - return code >1 / timeout / oversize / subprocess failure: safe `create_failed`
- Rollback unlock/remove 仍是 best-effort；subprocess failure 不会让 create 返回 `created=True`。
- Harness 文件已恢复为可读 UTF-8 中文清单，并同步当前 stage 边界。

## 已跑验证

- RED focused tests: 4 expected failures before implementation。
- Focused tests: `pytest tests/test_worktree_isolation.py -q` -> 20 passed。
- Adjacent regressions:
  `pytest tests/test_worktree_isolation.py tests/test_agent_harness_kernel.py tests/test_chat_api.py tests/test_repo_mutation_locking.py tests/test_verified_patch_promotion.py tests/test_worktree_reverification.py tests/test_worktree_disposal.py -q` -> 214 passed。
- `ruff check .` -> passed。
- `openspec validate --all` -> 23 passed, 0 failed。
- `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1` -> pytest 495 passed, 1 skipped; ruff, stage docs scan, skill eval structure scan passed。
- `git diff --check` -> passed, only CRLF normalization warnings。
- Archive 后 `openspec list` -> No active changes found。
- Archive 后 `openspec validate --all` -> 22 passed, 0 failed。
- Final implementation review: internal no P0/P1/P2；OpenCode reused `ses_1018bd2aeffeKLTCcQhhuQ1jFZ` and found no P0/P1/P2。P3 findings 已按 `reject/clarify` 与 `clarify` 处理。
- Focused Stage Debt Sweep: no blocking debt；`app/worktrees/disposal.py` 与 `app/worktrees/git_metadata.py` 的 subprocess hardening 是相邻剩余债，需另开小阶段。

## 下一步

- closeout 前检查 `git status --short --branch`、`git diff --name-only`、`git diff --check`。
- 若继续集成，先提交当前分支，再按项目规则合并/推送；不要混入新的 subprocess hardening 阶段。
