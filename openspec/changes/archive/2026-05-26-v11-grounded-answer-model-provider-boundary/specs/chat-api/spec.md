# chat-api Specification

## MODIFIED Requirements

### Requirement: 聊天响应包含审计字段

系统 SHALL 在每个成功聊天响应中返回 `trace_id`、`answer`、`related_files` 和 `tool_calls`。`answer` MAY 由 grounded answer pipeline 基于预算内仓库证据生成。系统 MUST NOT 为 V11 新增必需 `/chat` 顶层响应字段。

#### Scenario: Trace 响应结构

- **WHEN** 聊天请求成功完成
- **THEN** 响应包含以 `trace_` 开头的 `trace_id`
- **AND** 响应包含 `answer`、`related_files` 和 `tool_calls`
- **AND** 响应 MUST NOT 要求新的顶层 `citations`、`grounding`、`provider_audit` 或 `evidence_pack` 字段

#### Scenario: Grounded answer 不改变响应 schema

- **WHEN** `/chat` 通过 grounded answer pipeline 生成回答
- **THEN** grounded answer MUST 写入现有 `answer` 字段
- **AND** `tool_calls` MUST NOT 包含完整 prompt、完整模型输出、完整 Evidence Pack、API key 或内部 trace
