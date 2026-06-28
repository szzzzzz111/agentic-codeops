# 交接给下一轮 Chat

## 当前基线

- 当前分支：`codex/harden-git-metadata-output-bounds`。
- Active OpenSpec change：无。
- 最近归档 OpenSpec change：`harden-git-metadata-output-bounds`，归档到
  `openspec/changes/archive/2026-06-28-harden-git-metadata-output-bounds/`。
- 风险级别：high。
- 本阶段目标：修复 shared Git metadata runner 的 stdout pre-read hard cap 与 timeout
  kill/reap 代码债。
- Scope 只限 `app/worktrees/git_metadata.py`、`tests/test_worktree_disposal.py`、本 change
  的 OpenSpec/Harness 文档和真实状态文档。
- 本阶段不修改 destructive disposal `_run_mutation()`、worktree create helper、inspection
  streaming diff、re-verification runner、promotion state machine、public `/chat` contract、
  provider runtime、live eval、默认 CI、网络依赖、后台任务、runtime subagent、connector、
  notification、commit/merge/push automation、branch/PR automation 或 `git worktree prune`。

继续前先刷新 live state：

```powershell
git status --short --branch
git log -5 --oneline --decorate
openspec list
openspec validate --all
```

## 已完成内容

- OpenSpec planning 已完成，并经过 internal、Codex independent、OpenCode independent plan review。
- Plan findings 已按 `fix / clarify / reject / defer` 分类处理。
- 已实现 shared metadata bounded stdout pipe reader：
  - fixed argv + `shell=False`
  - `GIT_OPTIONAL_LOCKS=0`
  - `MAX_GIT_METADATA_BYTES = 256_000`
  - `GIT_METADATA_TIMEOUT_SECONDS = 10.0`
  - `GIT_METADATA_REAP_TIMEOUT_SECONDS = 1.0`
  - `GIT_METADATA_READER_JOIN_TIMEOUT_SECONDS = 1.0`
  - Windows-safe background stdout reader
  - timeout / oversize / read failure / reader non-completion / non-zero exit fail closed
- `git_metadata_text()` 与 `registry_entries()` public return shape 保持不变，继续把 unsafe
  metadata 映射为 `None`。
- Disposal postcheck metadata unavailable after mutation 继续是 failed disposal，不报告成功。

## 已跑验证

- RED evidence：新 metadata tests 初次触发旧实现缺口，包括 missing bounded reap constant /
  old temp-file capture 不能满足 pipe/cap-edge 断言。
- `pytest tests/test_worktree_disposal.py -k "git_metadata_runner" -q` -> 5 passed。
- `pytest tests/test_worktree_disposal.py -q` -> 38 passed。
- Adjacent regressions：
  - `pytest tests/test_worktree_inspection.py -q` -> 20 passed。
  - `pytest tests/test_worktree_reverification.py -q` -> 31 passed。
  - `pytest tests/test_verified_patch_promotion.py -q` -> 28 passed。
- `ruff check app/worktrees/git_metadata.py tests/test_worktree_disposal.py` -> passed。
- Final implementation review：OpenCode reused `ses_1018bd2aeffeKLTCcQhhuQ1jFZ`；无 P0/P1/P2。
  两个 P3（Popen start-failure coverage、reader thread name）已处理，focused re-review 确认关闭且无新 P0/P1/P2。
- `ruff check .` -> passed。
- `openspec validate --all` -> 23 passed, 0 failed。
- `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1` -> pytest 499 passed, 1 skipped；ruff、stage docs scan、skill eval structure scan passed。
- `git diff --check` -> passed, only CRLF normalization warnings。
- Focused Stage Debt Sweep：no blocking debt；残余相邻债仅为 `app/worktrees/disposal.py::_run_mutation()` destructive subprocess output cap，需独立阶段处理。
- Archive 后 `openspec list` -> No active changes found。
- Archive 后 `openspec validate --all` -> 22 passed, 0 failed。
- Archive 后 full `scripts/verify.ps1` -> pytest 499 passed, 1 skipped；ruff、stage docs scan、skill eval structure scan passed。

## 下一步

- merge/push 仍需用户明确授权。
