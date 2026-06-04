## MODIFIED Requirements

### Requirement: 聊天响应包含审计字段

系统 SHALL 在每个成功聊天响应中返回 `trace_id`、`answer`、`related_files` 和 `tool_calls`。`answer` MAY 由 grounded answer pipeline 基于预算内仓库证据生成，也 MAY 在明确 memory command、Long Task command、Assistant Control Surface 状态请求、Patch proposal 请求、明确 patch apply 确认、明确 verification run 请求或明确 Patch + Verify Loop 组合确认命中时返回确认、状态、步骤摘要、助手控制面摘要、patch proposal、apply 结果、验证结果摘要或组合摘要。系统 MUST NOT 为 V18 新增必需或可选 `/chat` 顶层响应字段。

#### Scenario: Patch Verify Loop 不改变响应 schema

- **WHEN** `/chat` 处理合法 Patch + Verify Loop 组合确认
- **THEN** 组合结果摘要 MUST 写入现有 `answer` 字段
- **AND** 响应 MUST 继续只要求 `trace_id`、`answer`、`related_files` 和 `tool_calls`
- **AND** 响应 MUST NOT 包含完整 diff、完整 stdout、完整 stderr、本机绝对路径、DB 路径、环境变量、API key 或内部 trace

#### Scenario: Verification run 不改变响应 schema

- **WHEN** `/chat` 处理明确 verification run 请求
- **THEN** 验证结果摘要 MUST 写入现有 `answer` 字段
- **AND** 响应 MUST 继续只要求 `trace_id`、`answer`、`related_files` 和 `tool_calls`
- **AND** 响应 MUST NOT 包含完整 stdout、完整 stderr、本机绝对路径、DB 路径、环境变量、API key 或内部 trace
