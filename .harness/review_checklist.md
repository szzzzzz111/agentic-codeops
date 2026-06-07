# 当前 Review 清单

当前活跃阶段：无 active implementation stage。

## V20 Planning / OpenSpec Gate

- [x] V20 plan 已锁定：单独 patch apply 与组合 Patch + Verify 进入 worktree，独立 verification 保持当前工作区语义。
- [x] OpenSpec change 包含 `worktree-isolation` 新能力与完整 stage planning / proposal / design / tasks。
- [x] OpenSpec change 覆盖被修改能力：`agent-loop-tool-execution`、`chat-api`、`safe-patch-authoring`、`patch-verify-loop`、`verification-runner`、`persistent-audit-recovery`、`harness-development-workflow`。
- [x] `execution_repo_path` 的内部传播机制明确，且不会进入公开响应、`ToolInvocationContext` 或持久审计。
- [x] `applied_in_worktree` 状态机、失败终态与重试语义在 spec / tasks 中明确。

## V20 Runtime Gate

- [x] `worktree_create` 作为受控高风险工具注册：`read_only=False`、`risk="write"`、`requires_approval=True`。
- [x] worktree 创建只允许固定 Git argv 和 `shell=False`，不接受用户提供的 Git 参数、路径、分支或 commit。
- [x] worktree 目录固定在 repo-local `.repopilot/worktrees/<worktree_id>`，成功创建后为 detached 且 locked。
- [x] 单独 patch apply 与组合 Patch + Verify 使用 worktree `execution_repo_path`；独立 verification 继续使用原始 `repo_path`。
- [x] worktree 创建前检查：非 bare Git 仓库、有效 `HEAD`、主工作区无 tracked 改动、无非 ignored untracked 文件、`.repopilot/` 被 Git ignore。
- [x] ignored 文件不阻止创建；非 ignored untracked 文件阻止创建。
- [x] worktree 创建失败或 metadata 写入失败会尽力回滚未完成创建，patch 保持 `pending`。
- [x] worktree 内 patch apply 失败时 patch 转 `failed`，不得运行 verification。
- [x] verification 失败时 patch 保持 `applied_in_worktree`，worktree 保留，V20 不提供重跑。
- [x] 不修改主工作区文件，不把成功 patch 误报为已写回主工作区。

## V20 Audit / Query Gate

- [x] `.repopilot/worktrees.sqlite3` 按 `user_id + repo_key` 隔离。
- [x] 支持 `查看 worktree <worktree_id>` / `worktree status <worktree_id>` 只读查询。
- [x] 缺失 worktree store 查询不创建状态目录或数据库。
- [x] worktree 生命周期事件写入持久审计，且不持久化绝对路径、`.git` 路径、Git stdout/stderr、完整 diff 或 secret。
- [x] `/chat` 顶层 schema 保持不变；结果仅通过 `answer`、`related_files`、`tool_calls` 返回。

## V20 Test Gate

- [x] 新增真实 Git worktree 测试，覆盖 detached + locked 创建。
- [x] 覆盖 dirty、非 ignored untracked、非 Git、bare、无 `HEAD`、`.repopilot/` 未忽略拒绝路径。
- [x] 覆盖单独 patch 与组合流程都不污染主工作区。
- [x] 覆盖 worktree 创建失败 / apply 失败不运行 verification。
- [x] 覆盖 verification 失败时状态与保留语义。
- [x] 覆盖独立 verification 仍在主工作区执行。
- [x] 覆盖跨用户 / 跨 repo worktree 查询隔离与 no-create read。

## V20 Stage Debt Sweep / Closeout Gate

- [x] Stage Debt Sweep 扫描 current docs、harness docs、active OpenSpec、long-term specs、changed runtime paths 和 adjacent runtime paths。
- [x] `README.md`、`docs/ARCHITECTURE.md`、`docs/PROGRESS.md`、`HANDOFF_TO_NEXT_CHAT.md`、`docs/FEATURE_LIST.json` 与 V20 当前状态一致。
- [x] `openspec/specs/**/spec.md` 不保留 `TBD`、`TODO` 或 archive placeholder Purpose。
- [x] `scripts/check_stage_docs.ps1` 与相关 docs parity 测试同步覆盖 V20 路线图与边界。
- [x] 内部 final review 已完成，发现的 runtime / docs / design 问题已修复并重新验证。
- [x] 外部 review 已完成，用户确认无阻塞 findings。

## V20 Verification Evidence

- `pytest tests\test_worktree_isolation.py -q`：14 passed。
- `pytest -q`：206 passed, 1 skipped。
- `openspec validate --all`：16 passed, 0 failed。
- `powershell -ExecutionPolicy Bypass -File scripts\verify.ps1`：通过。
- `git diff --check`：通过，仅有 CRLF 换行提示。

## V20 Internal Review Findings

- 已修复 metadata 持久化失败未捕获 `sqlite3.Error`，导致 worktree 不回滚的问题。
- 已修复 locked worktree 回滚前未 unlock，导致 Git 注册残留的问题。
- 已修复 worktree id 冲突时可能误删既有 worktree 的问题。
- 已补 AgentLoop 创建失败时 patch 保持 `pending` 且不运行 apply / verification 的测试。
- 已修正 README 当前态冲突与 design 中 `WorktreeCreateResult` 字段 / 方法签名偏差。

## V20 Archive / Handoff Gate

- [x] Implementation commit：`8be9b37 Add V20 worktree isolation`。
- [x] OpenSpec archive：`openspec/changes/archive/2026-06-07-v20-worktree-isolation/`。
- [x] 7 个 `ADDED Requirements` 已同步到长期 specs，无 `MODIFIED/REMOVED` 同步风险。
- [x] Archive 后 full verify、closeout gate 与 handoff parity 已完成。

Archive 后验证证据：

- `openspec validate --all`：15 passed, 0 failed。
- `powershell -ExecutionPolicy Bypass -File scripts\verify.ps1`：206 passed, 1 skipped；ruff、stage docs drift scan、skill eval structure scan 均通过。
- `powershell -ExecutionPolicy Bypass -File scripts\check_stage_closeout.ps1`：通过。
