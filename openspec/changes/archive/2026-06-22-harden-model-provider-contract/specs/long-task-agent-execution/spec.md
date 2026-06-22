## MODIFIED Requirements

### Requirement: Long Task plan 使用模板和受控 provider 增强

系统 SHALL 默认使用 deterministic task-type templates 生成 3-5 个 step。模板 MUST 覆盖
`code_location`、`implementation_explanation`、`call_relationship`、`test_or_validation`、
`file_summary`、`stage_planning` 和 `unknown`。所有 V14 step 的 `action_type` MUST 为
`repo_rag`。

显式配置真实 ModelProvider 时，系统 MAY 请求 provider 返回 JSON plan 增强模板字段。Planner MUST
使用 `json_object` output mode，并显式提供只包含 Planner JSON shape 的 structured output
instruction。Planner query MUST NOT 重复拼接 JSON 格式指令。Provider MUST NOT 改变 step 数、
顺序或 `action_type`。

Planner MUST 在解析 provider content 前显式确认 provider status 为 success。provider status
非 success、非法 JSON、非 object JSON 或业务 schema 校验失败时，系统 MUST 使用 deterministic
fallback plan 并记录 `plan_source=deterministic_fallback`。

#### Scenario: stage_planning 只在明确长任务指令中触发

- **WHEN** 用户发送包含阶段、OpenSpec 或规划词的创建长任务指令
- **THEN** planner MAY 选择 `stage_planning` 模板
- **AND** 普通 repo_search 的 QueryUnderstanding 行为不因此改变

#### Scenario: Planner 显式描述 JSON 输出

- **WHEN** provider-assisted planning 被启用
- **THEN** Planner MUST 使用自己的 structured output instruction
- **AND** query content MUST 只包含任务上下文和模板步骤，不重复 JSON shape 指令

#### Scenario: provider status 非成功时直接 fallback

- **WHEN** provider response status 不是 success
- **THEN** Planner MUST 使用 deterministic fallback plan
- **AND** Planner MUST NOT 尝试解析 provider content

#### Scenario: provider 输出非法时 fallback

- **WHEN** provider planning 返回非法 JSON、非 object JSON 或非法 step schema
- **THEN** 系统使用 deterministic template 创建任务
- **AND** 回答或内部 audit 标记 fallback plan source
