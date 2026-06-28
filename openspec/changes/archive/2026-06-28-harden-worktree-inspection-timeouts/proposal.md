## Why

`docs/PROGRESS.md` 当前记录的首个代码债是 `app/worktrees/inspection.py` 中 V21
worktree inspection 的 streaming Git diff 路径仍直接使用 `subprocess.Popen`，在流消费后
调用 `process.wait()` 时没有独立 timeout。恶意、异常或卡住的 Git 进程可能让只读
inspection 长时间挂起。

V21 已经要求 inspection 是 read-only、bounded、redacted，并且 metadata Git 命令已通过
`run_git_metadata()` 具备 timeout 与 byte cap；本 change 只补齐 streaming diff / hunk
count / preview 的 bounded timeout 与 fail-closed partial 语义。

## What Changes

- 为 `inspection.py` 中 streaming Git diff 读取增加 timeout-bounded process handling：
  - fixed argv、`shell=False`、`GIT_OPTIONAL_LOCKS=0` 继续保持。
  - hunk count 和 per-file preview 必须有覆盖“读流 + process wait”的总 deadline。
  - timeout、blocked read、non-zero exit 或 process error 必须 kill / reap 子进程，并返回 safe partial。
  - partial 不暴露 raw exception、本机路径、raw diff、stderr 或 unbounded stdout。
- 保持 existing public `/chat.answer` shape 与 worktree inspection response contract。
- 保持 preview 文件数、字符数、行数、单行长度、redaction、unsafe path omission 和 untracked
  count-only 语义。
- 从 `docs/PROGRESS.md` 已知剩余代码债中移除或改写该项，并记录本阶段 evidence。

## Capabilities

### New Capabilities

- None. This is hardening for an existing worktree inspection capability.

### Modified Capabilities

- `worktree-inspection`: strengthen streaming Git diff handling so inspection cannot hang indefinitely on hunk count or preview subprocess reads/waits.

## Impact

- OpenSpec planning files:
  `openspec/changes/harden-worktree-inspection-timeouts/**`.
- Harness files:
  `.harness/allowed_files.md`, `.harness/review_checklist.md`.
- Candidate implementation files after confirmation:
  `app/worktrees/inspection.py`, `tests/test_worktree_inspection.py`,
  `docs/PROGRESS.md`, `HANDOFF_TO_NEXT_CHAT.md`, and
  `openspec/specs/worktree-inspection/spec.md` at archive time.
- Out of scope:
  worktree creation / rollback subprocess hardening in `app/worktrees/manager.py`,
  destructive disposal/reconciliation behavior, re-verification, promotion, repo mutation locking,
  public `/chat` schema, provider runtime, live eval, default CI, network dependencies,
  `git worktree prune`, commit/merge/push automation, branch/PR automation, background tasks,
  runtime subagents, connectors, and notifications.
