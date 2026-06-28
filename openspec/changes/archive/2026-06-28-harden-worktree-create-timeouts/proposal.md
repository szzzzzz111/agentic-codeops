## Why

`docs/PROGRESS.md` 当前记录的首个剩余代码债是 `app/worktrees/manager.py` 中 V20
worktree create、workspace preflight 和 rollback 的 Git subprocess 调用没有独立 timeout，
且 `capture_output=True` 没有读取前输出硬上限。

Worktree creation 是 RepoPilot patch flow 的写风险入口。即使所有 Git argv 当前都是固定列表，
异常、卡住或输出异常膨胀的 Git 进程仍可能让 patch confirmation path 长时间挂起，或把不必要的
raw output 留在异常对象里。本 change 只补齐 worktree create / rollback Git subprocess 的 bounded
timeout、bounded output 和 fail-closed 语义。

## What Changes

- 为 `app/worktrees/manager.py` 的 Git subprocess helper 增加固定 timeout 和输出硬上限：
  - `rev-parse`、`status --porcelain`、`worktree add`、`worktree unlock`、`worktree remove`、
    `check-ignore` 都必须使用 fixed argv、`shell=False`、`GIT_OPTIONAL_LOCKS=0`。
  - stdout / stderr 必须在读取前受 hard cap 约束；timeout、oversize、non-zero exit 或 subprocess
    error 均安全降级为现有 create failure / rollback best-effort 语义。
  - public result 不暴露 raw stdout、stderr、traceback、本机绝对路径、`.git` 路径或 DB 路径。
- 保持现有 worktree create preconditions、detached locked worktree layout、patch flow、state
  transition 和 `/chat.answer` public contract。
- 保持 rollback best-effort：如果 metadata persistence 或 create 后续步骤失败，仍尝试 unlock /
  remove / local directory cleanup；rollback subprocess timeout 不得挂住 primary flow。
- 从 `docs/PROGRESS.md` 已知剩余代码债中移除或改写 `manager.py` 该项，并记录本阶段 evidence。

## Capabilities

### New Capabilities

- None. This is hardening for the existing worktree isolation create path.

### Modified Capabilities

- `worktree-isolation`: strengthen worktree creation, preflight, and rollback Git subprocess handling so patch
  confirmation cannot hang indefinitely or read unbounded Git output during worktree setup/cleanup.

## Impact

- OpenSpec planning files:
  `openspec/changes/harden-worktree-create-timeouts/**`.
- Harness files:
  `.harness/allowed_files.md`, `.harness/review_checklist.md`.
- Candidate implementation files after approval:
  `app/worktrees/manager.py`, `tests/test_worktree_isolation.py`,
  `docs/PROGRESS.md`, `HANDOFF_TO_NEXT_CHAT.md`, and
  `openspec/specs/worktree-isolation/spec.md` at archive time.
- Out of scope:
  `app/worktrees/inspection.py`, disposal/reconciliation, re-verification, verified promotion,
  repo mutation locking, `ToolExecutor`, `PermissionPolicy`, `ApprovalGate`, public `/chat` schema,
  provider runtime, live eval, default CI, network dependencies, `git worktree prune`,
  commit/merge/push automation, branch/PR automation, background tasks, runtime subagents,
  connectors, and notifications.
