# 交接给下一轮 Chat

## 当前基线（2026-06-28，repo mutation locking archived）

- 当前分支：`codex/harden-repo-mutation-locking`。
- Active OpenSpec change：无。
- 最近完成阶段：`harden-repo-mutation-locking`，已归档到
  `openspec/changes/archive/2026-06-28-harden-repo-mutation-locking/`。
- 阶段目标：为 RepoPilot-owned patch/worktree/verification/promotion write-risk flows
  增加 repo-key scoped mutation lock，关闭 V25 后记录的极窄跨进程 HEAD/file/state race。
- 本阶段不修改 `/chat` public contract、provider runtime、live eval、默认 CI、网络依赖、
  后台任务、runtime subagent、connector、notification、commit/merge/push automation、
  branch/PR automation 或 `git worktree prune`。

## 已完成内容

- 新增 repo-local SQLite mutation lock store。
- write-risk `ToolInvocationContext` 现在要求 lock provenance。
- AgentLoop 在 ordinary patch apply、组合 Patch + Verify、standalone verification、
  retained worktree re-verification、worktree disposal/reconciliation 和 verified promotion
  前获取 lock，并持有到 finalize/rollback/release。
- Lock conflict/unavailable 在 mutation 前 fail closed；acquired/released/release_failed
  通过 redacted `repo_mutation_lock` trace/audit summary 表达。
- standalone `verification_run` runner exception 已安全转为 `runner_error`，并释放 lock，
  不泄露本地路径、DB path、raw exception 或 secret。
- read-only inventory/inspection/status/repo search 不获取 mutation lock。

## 验证与 Review

- Focused lock tests：`pytest tests/test_repo_mutation_locking.py -q` 为 17 passed。
- Adjacent regression：
  `pytest tests/test_repo_mutation_locking.py tests/test_agent_harness_kernel.py tests/test_verified_patch_promotion.py tests/test_worktree_disposal.py tests/test_worktree_reverification.py tests/test_worktree_isolation.py tests/test_verification_runner.py tests/test_persistent_audit.py tests/test_chat_api.py -q`
  为 227 passed。
- `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`：通过，pytest 486 passed、
  1 skipped；ruff、stage docs scan、skill eval structure scan 均通过。
- Archive 后 `openspec list`：No active changes found。
- Archive 后 `openspec validate --all`：22 passed，0 failed。
- `git diff --check`：通过，仅有 CRLF normalization warnings。
- Internal implementation review、Codex independent final review、OpenCode final review 和
  Stage Debt Sweep 均完成；无未处理 P0/P1/P2。

## 下一步

继续前先查询 live state：

```powershell
git status --short --branch
git log -5 --oneline --decorate
openspec list
openspec validate --all
```

安全下一步：若本阶段尚未提交、合并或推送，先完成 Git closeout；不要混入新的 runtime
stage 或 skill/workflow 文档 hardening。
