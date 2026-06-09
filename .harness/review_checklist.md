# 当前 Review 清单

当前活跃阶段：V21 Worktree Inventory / Inspection（implementation 已提交，等待 archive 确认）。

## V21 Planning / OpenSpec Gate

- [x] V21 仅提供按 `user_id + repo_key` 隔离的纯只读 inventory / inspection。
- [x] OpenSpec change 包含 stage planning、proposal、design、tasks 与全部 spec deltas。
- [x] V21 inspection 明确替代 V20 status 查询；`worktree_status` trace event 替换为 `worktree_inspection`。
- [x] `/chat` 顶层 contract 保持 `trace_id`、`answer`、`related_files`、`tool_calls`。
- [x] 非目标明确排除 re-verification、cleanup、discard、promotion、主工作区写入、commit/merge/push、后台任务、subagents、connectors 与前端。

## V21 Read-Only / Scope Gate

- [x] Inventory 默认只返回当前 scope 最近 20 条记录，并稳定排序。
- [x] 缺失 worktree store、目录、Git registry 或 audit DB 的读取不得创建 `.repopilot/`、数据库或修改状态。
- [x] Inventory / inspection 不调用 `repo_rag`、verification、patch、cleanup 或任何写入工具。
- [x] 跨用户、跨 repo worktree 不得被列出或检查。
- [x] Untracked 文件只公开 count，不公开名称、路径前缀或内容。

## V21 Git / Preview Gate

- [x] Preview 路径只来自 `git diff --name-only -z --no-ext-diff --no-textconv <base_commit> --`。
- [x] Diffstat 只来自固定 argv 的 `git diff --numstat -z --no-ext-diff --no-textconv <base_commit> --`。
- [x] 用户消息和 metadata changed-files 不得驱动 per-file diff。
- [x] Per-file preview 使用固定 argv，并在执行前通过 repo-relative、非隐藏、非敏感、非二进制校验。
- [x] Patch body 与 aggregate hunk count 使用流式消费，不通过无界 `capture_output=True` 保留 raw diff；metadata Git 输出有显式上限。
- [x] Preview 最多 20 文件、总计 6000 字符、每文件 80 行、单行 300 字符。
- [x] Preview 拒绝二进制、敏感文件、隐藏目录、`.git/**` 与 `.repopilot/**`。
- [x] Preview 脱敏绝对路径、DB 路径、常见 secret 和 credential 赋值，并报告 omitted/truncated 计数。
- [x] Raw Git diff 不进入公开模型、trace、tool call 或 persistent audit。
- [x] Metadata scalar 与 tracked changed-file 摘要经过 bounded public formatter；tracked path 最多公开 20 条并报告 omitted count。
- [x] Git 读取设置 `GIT_OPTIONAL_LOCKS=0`，SQLite 读取使用 `mode=ro&immutable=1`，损坏 store 安全降级。
- [x] Preview 为空时仍报告 omitted/truncated counters，diffstat 明确报告 binary file count。

## V21 Inspection / Audit Gate

- [x] Inspection 返回 lifecycle、patch/base、tracked changed files、diffstat、hunk count、verification summary 与 registry/directory/metadata 一致性结果。
- [x] `AgentLoop.run()` 统一 wrapper 保持不变；`_skip_persistent_audit_for_result()` 检测 `worktree_inventory` / `worktree_inspection`。
- [x] Inventory / inspection 保留当前请求内脱敏 trace，但整次请求不写 persistent audit。
- [x] 已有 audit DB 的记录数在 inspection 后不变；缺失 audit DB 时不创建状态。
- [x] V21 closeout 记录 audit skip trade-off 与确定性测试证据：targeted regression 证明已有 audit row count 不变且 missing state 不创建 `.repopilot/`。

## V21 Verification / Closeout Gate

- [x] `docs/FEATURE_LIST.json` 在实现与全量验证完成前保持 V21 `passes: false`，全量验证通过后更新为 `true`。
- [x] 运行 V21 targeted pytest、`openspec validate --all`、默认 verify 与 `git diff --check`。
- [x] Stage Debt Sweep 覆盖 current docs、harness、active OpenSpec、长期 specs、runtime 与 adjacent tests。
- [x] 内部 final review 已完成并修复有效 findings；预期 external review 完成前，不进入 commit/archive/merge/push。
- [x] External review 已完成，用户确认无阻塞 findings；commit/archive/merge/push 仍需阶段级确认。
