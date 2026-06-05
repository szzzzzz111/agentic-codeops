# 当前 Review 清单

当前活跃阶段：V18 closeout debt remediation。

## V18 Post-Merge / Handoff Debt Gate

- [x] `README.md`、`docs/PROGRESS.md` 和 `HANDOFF_TO_NEXT_CHAT.md` 必须记录 V18 已 fast-forward 合并到 `main` 并推送到 `agentic-codeops/main`，不得继续提示 archive 后 closeout 或 merge / push 决策。
- [x] `openspec/specs/**/spec.md` 不得保留 `TBD`、`TODO` 或 `created by archiving change...` 这类 Purpose 占位。
- [x] Stage Debt Sweep 结果必须沉淀到 `docs/PROGRESS.md` 和 `HANDOFF_TO_NEXT_CHAT.md`，不得只留在聊天里。
- [x] `scripts/check_stage_docs.ps1` 必须扫描当前 durable docs、harness docs 和 long-term specs，并能拦截 stale branch、stale merge / push 建议和 archive 生成的 Purpose 占位。
- [x] branch cleanup / retention 必须显式记录；已合并 feature 分支若保留，必须说明其已 fully merged 且与 `main` 同 hash。
- [x] 本次不得实现 V19 Persistent Audit / Recovery runtime；V19 必须另起 OpenSpec change 后再开始。

## V18 Archive Closeout Gate

- [x] V18 implementation commit 已创建：`e76807d Add V18 patch verify loop`。
- [x] V18 external review 已处理并确认无阻塞。
- [x] V18 active change 已归档到 `openspec/changes/archive/2026-06-04-v18-patch-verify-loop/`。
- [x] 长期 specs 已通过 `openspec archive v18-patch-verify-loop -y` 同步，新增 `openspec/specs/patch-verify-loop/spec.md`。
- [x] `openspec list` 显示 no active changes。
- [x] V18 archive 后 OpenSpec 全量验证通过。
- [x] V18 archive 后默认验证通过。
- [x] V18 archive closeout gate 通过。
- [x] 下一阶段开始前必须先创建新 OpenSpec change，并同步 `.harness/allowed_files.md` 和 `.harness/review_checklist.md`。

## V18 Planning / Implementation Gate

- [x] V18 OpenSpec change 包含 `stage_planning.md`、proposal、design、tasks，以及 `patch-verify-loop`、`safe-patch-authoring`、`verification-runner`、`agent-loop-tool-execution`、`chat-api` 和 `harness-development-workflow` spec delta。
- [x] `.harness/allowed_files.md` 已同步 V18 写入边界。
- [x] `openspec validate v18-patch-verify-loop` 通过。
- [x] AgentLoop 前置顺序固定为 Memory command、Long Task command、Assistant Control Surface、Patch command / Patch intent（含组合确认）、Verification intent、capability-status、repo_search/chat_only。
- [x] 组合确认必须在 Patch command 分支内优先处理；优先级为 `组合确认 > 纯 verification intent > capability-status/repo_search`。
- [x] 组合确认 parser 必须同时解析 `patch_id` 和 verification label；缺失 label、半解析、只能解析出 patch id 时，不得默认补 `verify`，不得 apply。
- [x] 组合确认中的 verification label 只接受 `verify`、`pytest` 和 `ruff`；不得接受附加参数、管道、重定向、环境变量赋值、任意 shell 文本或 `ruff --fix`。
- [x] 非法组合请求必须整体拒绝，不执行 `patch_apply`，不触发 `verification_run`。
- [x] 单独 `确认 patch <patch_id>` / `应用 patch <patch_id>` 保持 V16 apply-only 行为，不自动验证。
- [x] 组合流程必须先通过 `PatchManager.prepare_apply` 和 `patch_apply` 权限审批链路；apply 成功后才允许进入 verification。
- [x] verification 必须使用独立 `ToolInvocationContext`，字段包含 `tool_name=verification_run`、`intent=verification_run`、`command_label`、`confirmed=true`、`scope_valid=true/false`，不得复用 patch context。
- [x] patch apply 失败、过期、hash mismatch、跨用户、跨 repo、非 pending 或 scope invalid 时，不生成 verification context，不运行验证。
- [x] `patch_apply` 和 `verification_run` 均必须通过 `ToolRegistry -> PermissionPolicy -> ApprovalGate -> ToolExecutor`。
- [x] API handler、parser 和 AgentLoop 不得直接调用 subprocess；实际验证只能通过 `ToolExecutor.verification_run(...)`。
- [x] 公开 `answer` 和 `tool_calls` 不得泄露完整 diff、完整 stdout/stderr、本机绝对路径、DB 路径、环境变量、API key、完整 internal trace、完整 Evidence Pack 或 provider prompt/output。
- [x] `/chat` 顶层响应 contract 不新增必需或可选字段；组合结果只进入现有 `answer` 和安全 `tool_calls` 摘要。
- [x] 验证失败只返回失败摘要和下一步建议；不得自动生成 patch、自动再次 apply、commit、push、创建 worktree 或调度 subagent。
- [x] 默认验证不依赖真实网络、API key、真实模型输出、外部队列或外部数据库。

## Historical Gates

- V17 Verification Runner 已归档到 `openspec/changes/archive/2026-06-03-v17-verification-runner/`。
- V16 Safe Patch Authoring 已归档到 `openspec/changes/archive/2026-05-31-v16-safe-patch-authoring/`。
- V1-V18 active changes 均已归档；历史 review 明细保留在 git history 和 archived OpenSpec change 中。
