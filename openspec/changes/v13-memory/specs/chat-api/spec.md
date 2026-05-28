# chat-api Specification

## MODIFIED Requirements

### Requirement: 聊天响应包含审计字段

系统 SHALL 在每个成功聊天响应中返回 `trace_id`、`answer`、`related_files` 和 `tool_calls`。`answer` MAY 由 grounded answer pipeline 基于预算内仓库证据生成，也 MAY 在明确 memory command 命中时返回 memory 写入或删除确认。系统 MUST NOT 为 V13 新增必需 `/chat` 顶层响应字段。

#### Scenario: Memory 不改变响应 schema

- **WHEN** `/chat` 处理 memory command 或普通请求 memory read
- **THEN** memory 结果或确认 MUST 写入现有 `answer` 字段
- **AND** 响应 MUST 继续只要求 `trace_id`、`answer`、`related_files` 和 `tool_calls`
- **AND** `tool_calls` MUST NOT 包含完整 memory value、DB 路径、本机绝对路径或内部 trace
