# chat-api Specification

## MODIFIED Requirements

### Requirement: 聊天响应包含审计字段

系统 SHALL 在每个成功聊天响应中返回 `trace_id`、`answer`、`related_files` 和 `tool_calls`。`answer` MAY 由 grounded answer pipeline 基于预算内仓库证据生成，也 MAY 在明确 memory command 或 Long Task command 命中时返回确认、状态或步骤摘要。系统 MUST NOT 为 V14 新增必需 `/chat` 顶层响应字段。

#### Scenario: Long Task 不改变响应 schema

- **WHEN** `/chat` 处理 Long Task 创建、查看、列出、暂停、恢复、补充、reopen 或归档命令
- **THEN** Long Task 结果 MUST 写入现有 `answer` 字段
- **AND** 响应 MUST 继续只要求 `trace_id`、`answer`、`related_files` 和 `tool_calls`
- **AND** `tool_calls` MUST NOT 包含完整 scratch、完整 ReAct trace、完整 provider output、DB 路径、本机绝对路径或内部 trace
