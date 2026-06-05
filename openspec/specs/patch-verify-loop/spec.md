# patch-verify-loop Specification

## Purpose
定义 RepoPilot 在明确组合确认下串联 pending patch apply 与白名单验证的运行时边界。该能力只覆盖 apply 成功后立即执行受控验证并返回脱敏组合摘要，不包含持久审计、自动修复、worktree、commit/push 或 subagent 调度。
## Requirements
### Requirement: Patch Verify Loop 只由明确组合确认触发

系统 SHALL 只在用户发送明确组合确认请求时触发 Patch + Verify Loop。组合确认 MUST 同时包含有效 pending patch id 和可归一化的 verification label。组合确认 MUST 在 Patch command 分支内优先于纯 Verification intent 处理，并且 MUST NOT 被 capability-status 或 repo_search 捕获。

组合确认的 verification label MUST 只允许 `verify`、`pytest` 或 `ruff`，其中 `验证` / `verify` 对应 `verify` 标签。组合请求缺失 label、只能解析出 patch id、包含非白名单 label、附加参数、管道、重定向、环境变量赋值或 shell 语法时，系统 MUST 拒绝整个组合请求，MUST NOT 执行 `patch_apply`，并且 MUST NOT 触发 `verification_run`。

#### Scenario: 合法组合确认触发闭环

- **WHEN** 用户发送 `确认 patch patch_abc 并运行验证`
- **THEN** 系统 SHALL 将 patch id 解析为 `patch_abc`
- **AND** 系统 SHALL 将 verification label 归一化为 `verify`
- **AND** 系统 MAY 进入 patch apply 权限审批链路

#### Scenario: 缺失 label 的组合请求不默认 apply

- **WHEN** 用户发送类似组合确认但未提供 verification label
- **THEN** 系统 MUST 拒绝整个组合请求
- **AND** 系统 MUST NOT 执行 `patch_apply`
- **AND** 系统 MUST NOT 运行验证

#### Scenario: 非白名单验证标签整体拒绝

- **WHEN** 用户发送 `确认 patch patch_abc 并运行 pytest tests/test_x.py`
- **THEN** 系统 MUST 拒绝整个组合请求
- **AND** 系统 MUST NOT 执行 `patch_apply`
- **AND** 系统 MUST NOT 运行验证

### Requirement: Patch Verify Loop 按 apply 后 verify 顺序执行

系统 SHALL 在合法组合确认中先通过既有 `PatchManager.prepare_apply`、`PermissionPolicy`、`ApprovalGate` 和 `ToolExecutor.patch_apply` 应用 pending patch。只有 patch apply 成功后，系统 SHALL 创建独立 verification `ToolInvocationContext` 并通过 `PermissionPolicy`、`ApprovalGate` 和 `ToolExecutor.verification_run` 运行白名单验证。

verification context MUST 使用 `tool_name="verification_run"`、`intent="verification_run"`、`command_label=<label>`、`confirmed=True` 和 repo scope 校验结果。系统 MUST NOT 复用 patch apply context 作为 verification context。patch apply 失败、pending patch 过期、hash mismatch、非 pending、跨用户、跨 repo 或 scope invalid 时，系统 MUST NOT 创建 verification context，MUST NOT 运行验证。

#### Scenario: apply 成功后运行验证

- **WHEN** pending patch 有效且 apply 成功
- **THEN** 系统 SHALL 将 patch 标记为 applied
- **AND** 系统 SHALL 使用独立 verification context 运行白名单验证
- **AND** `/chat.tool_calls` MAY 包含 `patch_apply` 和 `verification_run` 两条安全摘要

#### Scenario: apply 失败不运行验证

- **WHEN** pending patch apply 失败
- **THEN** 系统 MUST 返回 apply 失败摘要
- **AND** 系统 MUST NOT 调用 `ToolExecutor.verification_run`

### Requirement: Patch Verify Loop 公开响应保持安全 contract

系统 SHALL 通过现有 `/chat.answer` 返回 Patch + Verify Loop 的组合摘要，并通过现有 `tool_calls` 返回安全工具调用摘要。系统 MUST NOT 为 V18 新增 `/chat` 顶层字段。

公开响应 MUST NOT 包含完整 diff、完整 stdout、完整 stderr、完整 internal trace、本机绝对路径、DB 路径、环境变量、API key、完整 Evidence Pack 或 provider prompt/output。验证失败时系统 SHALL 返回失败摘要和下一步修复建议，但 MUST NOT 自动生成 patch、再次 apply、commit、push、创建 worktree 或调度 subagent。

#### Scenario: 组合响应保持 chat contract

- **WHEN** `/chat` 返回 Patch + Verify Loop 结果
- **THEN** 响应 MUST 继续只包含 `trace_id`、`answer`、`related_files` 和 `tool_calls`
- **AND** `answer` MUST NOT 包含完整 diff 或完整 stdout/stderr

