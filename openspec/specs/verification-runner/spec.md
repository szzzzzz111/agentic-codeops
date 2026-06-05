# verification-runner Specification

## Purpose
定义 RepoPilot 在明确验证请求下运行固定白名单验证命令的边界。该能力要求验证执行通过 `ToolExecutor.verification_run`、权限审批上下文、固定 cwd、timeout 和输出脱敏完成，不开放任意 shell 或用户自定义命令参数。
## Requirements
### Requirement: Verification Runner 只执行明确验证请求

系统 SHALL 只在用户发送明确验证请求时触发 Verification Runner。验证请求 MUST 解析为白名单命令标签，MUST NOT 接受任意 shell 文本、附加参数、管道、重定向或环境变量注入。

白名单 SHALL 只包含 `pytest`、`ruff` 和 `verify` 三个稳定标签。`verify` SHALL 映射到 `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`。系统 MAY 支持中英文触发词，但 MUST 在执行前归一化为白名单标签。

V18 Patch + Verify Loop 中的 verification label MUST 复用同一白名单语义。组合确认中的 verification label 非白名单、含参数、含 shell 语法或缺失时，系统 MUST 拒绝整个组合请求，MUST NOT 先 apply patch 后再拒绝 verification。

#### Scenario: 明确验证请求触发白名单命令

- **WHEN** 用户发送 `运行 pytest`
- **THEN** 系统 SHALL 将请求解析为 `pytest` 标签
- **AND** 系统 MAY 进入 `verification_run` 权限审批链路

#### Scenario: 任意 shell 文本被拒绝

- **WHEN** 用户发送包含管道、重定向、环境变量赋值或额外 shell 参数的验证请求
- **THEN** 系统 MUST 拒绝执行
- **AND** 系统 MUST 返回支持的白名单命令标签摘要

#### Scenario: 组合确认中的非法验证标签拒绝整个组合

- **WHEN** 用户发送 `确认 patch patch_abc 并运行 ruff --fix`
- **THEN** 系统 MUST 拒绝整个组合请求
- **AND** 系统 MUST NOT 执行 `patch_apply`
- **AND** 系统 MUST NOT 运行验证

### Requirement: verification_run 必须经过权限审批边界

系统 SHALL 将 `verification_run` 注册到 `ToolRegistry`。`verification_run` MUST 标记为 `read_only=False`、`risk="write"`、`requires_approval=True`，因为验证命令可能创建缓存文件或执行项目脚本。

系统 MUST 继续使用 `PermissionPolicy` 和 `ApprovalGate` 的三态模型。`PermissionPolicy` MUST 只产出 `allow`、`deny` 或 `ask`。有效 verification context MAY 让 `verification_run` 进入 `ask -> ApprovalGate pass`；缺少有效 context、非白名单标签或 repo scope 无效时 MUST 拒绝执行。

#### Scenario: 有效验证上下文通过审批

- **WHEN** `verification_run` 已注册且 context 包含有效白名单标签和 repo scope
- **THEN** `PermissionPolicy` 返回 `ask`
- **AND** `ApprovalGate` 判定通过
- **AND** AgentLoop MAY 调用 `ToolExecutor.verification_run`

#### Scenario: 无效验证上下文被拒绝

- **WHEN** `verification_run` 缺少有效 context 或命令标签不在白名单内
- **THEN** `PermissionPolicy` 返回 `deny`
- **AND** AgentLoop MUST NOT 调用 runner

### Requirement: 验证执行必须限制 cwd、timeout 和输出

系统 SHALL 只通过 `ToolExecutor.verification_run(...)` 执行验证。runner MUST 使用 argv list 执行命令，MUST NOT 使用 shell 字符串执行。执行 cwd MUST 限制为 resolved `repo_path`。

runner SHALL 为每次验证设置固定 timeout。stdout 和 stderr MUST 各最多保留 4000 字符。`/chat.answer` 中验证输出摘要总计 MUST 最多保留 6000 字符，并 MUST 标记 `truncated=true/false`。timeout、命令缺失、非零退出码和 runner 异常 MUST 返回结构化失败摘要，而不是破坏 `/chat` 请求。

#### Scenario: 非零退出码返回失败摘要

- **WHEN** 白名单验证命令以非零退出码结束
- **THEN** 系统 SHALL 返回 failed 状态、exit code 和截断后的输出摘要
- **AND** `/chat` 请求本身仍返回稳定 schema

#### Scenario: 验证命令超时

- **WHEN** 白名单验证命令超过固定 timeout
- **THEN** 系统 MUST 终止命令
- **AND** 系统 SHALL 返回 timed out 摘要

### Requirement: 验证公开响应必须脱敏

系统 SHALL 通过现有 `/chat.answer` 返回验证结果摘要，并通过 `tool_calls` 返回安全工具调用摘要。系统 MUST NOT 为 V17 新增 `/chat` 顶层字段。

公开响应 MUST NOT 包含完整 stdout、完整 stderr、本机绝对路径、DB 路径、环境变量、API key、完整 internal trace、完整 Evidence Pack 或 provider prompt/output。系统 MUST 将 resolved `repo_path` 替换为 `<repo>`，将 Windows / POSIX 本机绝对路径替换为 `<local-path>`，将 `.repopilot/...` 替换为 `.repopilot/<redacted>`，并将 `API_KEY=...`、`TOKEN=...`、`SECRET=...`、`PASSWORD=...` 整段替换为 `<redacted-secret>`。

#### Scenario: 验证响应保持 chat contract

- **WHEN** `/chat` 返回验证结果
- **THEN** 响应 MUST 继续只包含 `trace_id`、`answer`、`related_files` 和 `tool_calls`
- **AND** `answer` MUST NOT 包含完整 stdout 或完整 stderr

### Requirement: V17 不实现 Patch + Verify Loop

V17 SHALL 提供独立 Verification Runner。系统 MUST NOT 在 patch proposal 或 patch apply 后自动运行验证，MUST NOT 根据验证失败自动生成 patch，MUST NOT 持久化 verification result，MUST NOT 创建 worktree，MUST NOT commit 或 push。

#### Scenario: Patch apply 后不自动验证

- **WHEN** 用户确认应用 patch
- **THEN** 系统 MAY 执行 V16 patch apply
- **AND** 系统 MUST NOT 自动触发 `verification_run`
