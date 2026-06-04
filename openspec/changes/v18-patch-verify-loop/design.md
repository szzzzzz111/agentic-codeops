## Current Behavior

- `PatchManager.prepare_apply(...)` 只接受单独确认语法：`确认 patch <patch_id>`、`应用 patch <patch_id>`、`confirm patch <patch_id>`、`apply patch <patch_id>`。
- `VerificationRunner` 只接受单独验证请求，并归一化为 `pytest`、`ruff` 或 `verify`。
- AgentLoop 当前顺序为 Memory、Long Task、Assistant Control Surface、Patch command / Patch intent、Verification intent、capability-status、repo_search/chat_only。
- 单独 patch apply 后不会自动运行验证。

## Target Behavior

- Patch command 分支先检测组合确认请求。组合确认必须在进入纯 verification intent 前处理，避免含 `patch_id` 和验证词的请求被误当成单独 verification。
- 组合请求必须完整解析出：
  - `patch_id`
  - verification label: `verify`、`pytest` 或 `ruff`
- 合法组合请求先执行既有 patch apply 权限链路。只有 apply 成功后才创建独立 verification context 并执行验证。
- 组合响应把 apply 摘要和 verification 摘要串联到现有 `answer`；`tool_calls` 包含安全的 `patch_apply` 和 `verification_run` 摘要。

## Non-Goals

- 不新增 `/chat` 顶层字段或公开 API。
- 不支持 targeted pytest、用户附加参数、管道、重定向、环境变量赋值或任意 shell。
- 不持久化 verification result、不维护 attempt history、不做跨 session recovery。
- 不根据验证失败自动生成 patch、不自动再次 apply、不 commit/push、不创建 worktree、不调度 subagents。

## Data Returned And Not Returned

- 返回：
  - apply 成功/失败摘要。
  - verification command label、status、exit_code、duration、truncated 和截断脱敏输出。
  - 安全 `tool_calls` 摘要。
- 不返回：
  - 完整 diff。
  - 完整 stdout/stderr。
  - 完整 internal trace。
  - Evidence Pack、provider prompt/output、本机绝对路径、DB 路径、API key 或环境变量。

## Error Behavior

- 缺失 verification label、只能解析出 patch_id、非法 label、附加参数或 shell 语法：返回 unsupported verification answer，不执行 patch apply。
- pending patch 缺失、过期、非 pending、hash mismatch 或 scope invalid：沿用 patch apply 安全失败，不运行验证。
- patch apply preflight 或写入失败：状态标记为 failed，不运行验证。
- verification 非零退出码：返回验证失败摘要和下一步建议，不自动生成新 patch。
- verification unavailable/timeout：返回结构化摘要，不破坏 `/chat` schema。

## Security And Path Boundaries

- 组合 parser 不把用户原始 shell 文本传给 `ToolInvocationContext`。
- patch apply context 和 verification context 必须彼此独立。
- verification context 字段固定为 `tool_name="verification_run"`、`intent="verification_run"`、`command_label=<label>`、`confirmed=True`、`scope_valid=True/False`。
- `ToolExecutor.verification_run` 继续使用 argv list 和 `shell=False`。

## Trace / Audit

- 内部 trace 可记录：
  - `patch_verify_loop_started`
  - `patch_verify_apply_summarized`
  - `patch_verify_verification_summarized`
- trace summary 只记录状态、命令标签、退出码、耗时、truncated 等摘要，不记录完整输出或本机路径。
