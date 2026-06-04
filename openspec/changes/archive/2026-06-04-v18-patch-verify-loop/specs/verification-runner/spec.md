## MODIFIED Requirements

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
