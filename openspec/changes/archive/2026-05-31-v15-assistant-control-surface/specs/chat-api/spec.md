# chat-api Specification

## MODIFIED Requirements

### Requirement: 聊天响应包含审计字段

系统 SHALL 在每个成功聊天响应中返回 `trace_id`、`answer`、`related_files` 和 `tool_calls`。`answer` MAY 由 grounded answer pipeline 基于预算内仓库证据生成，也 MAY 在明确 memory command、Long Task command 或 Assistant Control Surface 状态请求命中时返回确认、状态、步骤摘要或助手控制面摘要。系统 MUST NOT 为 V15 新增必需或可选 `/chat` 顶层响应字段。

#### Scenario: Assistant Control Surface 不改变响应 schema

- **WHEN** `/chat` 处理明确 Assistant Control Surface 状态请求
- **THEN** 控制面结果 MUST 写入现有 `answer` 字段
- **AND** 响应 MUST 继续只要求 `trace_id`、`answer`、`related_files` 和 `tool_calls`
- **AND** `related_files` 和 `tool_calls` MUST 为空列表
- **AND** 响应 MUST NOT 包含完整 memory value、完整 scratch、完整 ReAct trace、完整 provider output、完整 Evidence Pack、DB 路径、本机绝对路径或内部 trace
