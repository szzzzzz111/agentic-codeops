# 当前 Review 清单

当前活跃阶段：V22 Worktree Re-verification（实现完成，等待 review）。

## V22 Planning / OpenSpec Gate

- [x] V22 仅提供按 `user_id + repo_key` 隔离的 retained worktree 明确 re-verification。
- [x] OpenSpec change 包含 stage planning、proposal、design、tasks 与全部 spec deltas。
- [x] 命令限定为 `worktree verify <worktree_id> <command_label>` 与 `重新验证 worktree <worktree_id> <command_label>`。
- [x] 只复用现有 `pytest`、`ruff`、`verify` 白名单，不新增标签或参数。
- [x] `/chat` 顶层 contract 保持 `trace_id`、`answer`、`related_files`、`tool_calls`。
- [x] 非目标明确排除 cleanup、discard、unlock/remove、reconciliation、promotion、patch mutation、主工作区写入、commit/merge/push、任意 shell、后台任务、subagents、connectors 与前端。
- [x] 内部 plan review 与 `openspec validate v22-worktree-re-verification --strict` 通过。
- [x] 用户明确确认实现前，不修改 runtime 或 tests。

## V22 Command / Scope Gate

- [x] 完整规范化消息必须精确匹配命令形状；部分匹配不得落入 standalone verification。
- [x] 附加参数、路径、环境变量、管道、重定向、shell syntax 与未知 label 在 Git/verification 前拒绝。
- [x] unknown、跨用户、跨 repo worktree id 使用相同安全 not-found 行为，并在 Git inspection 前停止。
- [x] 用户输入不得驱动 argv、cwd、worktree path、Git path、环境变量或 timeout。

## V22 Fail-Closed Preflight Gate

- [x] Preflight 只读取 scoped metadata 与必要一致性证据，不执行 V21 完整 diff/preview inspection。
- [x] expected directory 只从 trusted repo root、managed worktree root 与 scoped worktree id 派生。
- [x] `ready`、`create_failed`、`patch_failed` 与未知 lifecycle 在 Git inspection 前 fail closed；只允许 `patch_applied`、`verification_failed`、`verification_succeeded`。
- [x] 执行前验证 directory、Git registry membership、registry path equality 与 HEAD/base equality。
- [x] 任一缺失、不一致、损坏、Git 异常或 malformed output 均不得运行 verification。
- [x] Preflight failure 不 repair、reconcile、cleanup、unlock/remove、retry Git、创建未知 worktree 或修改主工作区。
- [x] Preflight/approval failure 保留原 worktree lifecycle，因为 verification 未执行。

## V22 Verification / State Gate

- [x] Re-verification 经过 `ToolRegistry -> PermissionPolicy -> ApprovalGate -> ToolExecutor.verification_run`。
- [x] Verification cwd 仅为 trusted retained worktree execution path，主工作区保持不变。
- [x] 复用现有固定 argv、`shell=False`、timeout、输出限长与脱敏逻辑。
- [x] 执行成功更新为 `verification_succeeded`；执行 non-success 更新为 `verification_failed`。
- [x] 不新增 `verification_rerun_*` lifecycle。
- [x] 成功、执行失败、preflight failure 后 patch 均保持 `applied_in_worktree`；不调用 patch manager/store/apply。

## V22 Audit / Contract Gate

- [x] 每个识别出的 re-verification 请求尝试写入一条 scoped、related-to-worktree 的脱敏 `verification_result` audit。
- [x] Audit 可区分 `attempt_kind=worktree_reverification`、execution attempted、preflight outcome 与每次结果。
- [x] Scoped matching audit event count 表达 rerun 次数，不新增 mutable counter 或 schema migration。
- [x] 完整 stdout/stderr、绝对路径、`.git`/DB 路径、环境变量、secret、raw Git output、diff 与 preview 不进入 answer、trace、tool call 或 audit。
- [x] `related_files` 保持空；preflight failure 不公开 verification tool call。
- [x] 不调用 repo RAG、patch apply、cleanup、reconciliation、promotion 或其他越界工具。
- [x] Git/verification 异常安全降级，不自动修复或重试。
- [x] Audit 写入失败遵循现有 best-effort 规则，不破坏 primary `/chat` result。

## V22 Verification / Closeout Gate

- [x] `docs/FEATURE_LIST.json` 在实现与全量验证完成前保持 V22 `passes: false`。
- [x] 运行 V22 targeted pytest、相关回归、`openspec validate --all`、默认 verify 与 `git diff --check`。
- [x] Stage Debt Sweep 覆盖 current docs、harness、active OpenSpec、长期 specs、runtime 与 adjacent tests。
- [x] 内部 final review 完成并修复有效 findings；external review 完成前不进入 commit/archive/merge/push。
