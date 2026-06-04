# 当前 Review 清单

当前活跃阶段：V18 Patch + Verify Loop。

## V18 Planning / Implementation Gate

- [ ] V18 OpenSpec change 包含 `stage_planning.md`、proposal、design、tasks，以及 `patch-verify-loop`、`safe-patch-authoring`、`verification-runner`、`agent-loop-tool-execution`、`chat-api` 和 `harness-development-workflow` spec delta。
- [ ] `.harness/allowed_files.md` 已同步 V18 写入边界。
- [ ] `openspec validate v18-patch-verify-loop` 通过。
- [ ] AgentLoop 前置顺序固定为 Memory command、Long Task command、Assistant Control Surface、Patch command / Patch intent（含组合确认）、Verification intent、capability-status、repo_search/chat_only。
- [ ] 组合确认必须在 Patch command 分支内优先处理；优先级为 `组合确认 > 纯 verification intent > capability-status/repo_search`。
- [ ] 组合确认 parser 必须同时解析 `patch_id` 和 verification label；缺失 label、半解析、只能解析出 patch id 时，不得默认补 `verify`，不得 apply。
- [ ] 组合确认中的 verification label 只接受 `verify`、`pytest` 和 `ruff`；不得接受附加参数、管道、重定向、环境变量赋值、任意 shell 文本或 `ruff --fix`。
- [ ] 非法组合请求必须整体拒绝，不执行 `patch_apply`，不触发 `verification_run`。
- [ ] 单独 `确认 patch <patch_id>` / `应用 patch <patch_id>` 保持 V16 apply-only 行为，不自动验证。
- [ ] 组合流程必须先通过 `PatchManager.prepare_apply` 和 `patch_apply` 权限审批链路；apply 成功后才允许进入 verification。
- [ ] verification 必须使用独立 `ToolInvocationContext`，字段包含 `tool_name=verification_run`、`intent=verification_run`、`command_label`、`confirmed=true`、`scope_valid=true/false`，不得复用 patch context。
- [ ] patch apply 失败、过期、hash mismatch、跨用户、跨 repo、非 pending 或 scope invalid 时，不生成 verification context，不运行验证。
- [ ] `patch_apply` 和 `verification_run` 均必须通过 `ToolRegistry -> PermissionPolicy -> ApprovalGate -> ToolExecutor`。
- [ ] API handler、parser 和 AgentLoop 不得直接调用 subprocess；实际验证只能通过 `ToolExecutor.verification_run(...)`。
- [ ] 公开 `answer` 和 `tool_calls` 不得泄露完整 diff、完整 stdout/stderr、本机绝对路径、DB 路径、环境变量、API key、完整 internal trace、完整 Evidence Pack 或 provider prompt/output。
- [ ] `/chat` 顶层响应 contract 不新增必需或可选字段；组合结果只进入现有 `answer` 和安全 `tool_calls` 摘要。
- [ ] 验证失败只返回失败摘要和下一步建议；不得自动生成 patch、自动再次 apply、commit、push、创建 worktree 或调度 subagent。
- [ ] 默认验证不依赖真实网络、API key、真实模型输出、外部队列或外部数据库。

## Historical Gates

- V17 Verification Runner 已归档到 `openspec/changes/archive/2026-06-03-v17-verification-runner/`。
- V16 Safe Patch Authoring 已归档到 `openspec/changes/archive/2026-05-31-v16-safe-patch-authoring/`。
- V1-V17 active changes 均已归档；历史 review 明细保留在 git history 和 archived OpenSpec change 中。
