## ADDED Requirements

### Requirement: 系统构建可审计 Evidence Pack

系统 SHALL 在 repo-local retrieval 成功后构建结构化 Evidence Pack。Evidence Pack MUST 至少包含原始查询、问题类型、retrieval mode、预算摘要和 evidence items。

每个 evidence item MUST 至少包含稳定 `evidence_id`、相对 `file_path`、1-based `start_line`、1-based `end_line`、`score`、`snippet`、`source_summary`、`included` 和 `truncated`。Evidence Pack MUST NOT 包含本机绝对路径或完整文件内容。

#### Scenario: retrieval result 被转换为 evidence item

- **WHEN** hybrid repo retrieval 返回带 citation 和 snippet 的结果
- **THEN** 系统 MUST 构建 Evidence Pack
- **AND** evidence item MUST 包含稳定 `evidence_id`、相对 `file_path`、`start_line`、`end_line`、`score`、`snippet`、`source_summary`、`included` 和 `truncated`
- **AND** evidence item MUST NOT 包含本机绝对路径

#### Scenario: 空 retrieval result 产生空 evidence pack

- **WHEN** repo retrieval 成功但没有返回结果
- **THEN** 系统 MUST 构建 evidence items 为空的 Evidence Pack
- **AND** 预算摘要 MUST 记录 included count 为 `0`
- **AND** `/chat` 顶层响应 MUST 继续保持现有 contract

### Requirement: 系统执行确定性 Context Budget

系统 SHALL 对 Evidence Pack 执行确定性 context budget。Context budget MUST 使用字符预算边界，默认 `max_context_chars` MUST 为稳定常量，并且 MUST 记录 `budget_used_chars`、`budget_remaining_chars`、`included_count`、`omitted_count` 和 `truncated_count`。

系统 MUST 按 retrieval 既有稳定排序纳入 evidence items。系统 MUST NOT 在 context budget 阶段执行 LLM rerank、query rewrite、context compression 或语义合并。

#### Scenario: evidence snippets 在预算内全部纳入

- **WHEN** evidence snippets 的总字符数不超过 `max_context_chars`
- **THEN** context budget MUST 纳入全部 evidence items
- **AND** `omitted_count` MUST 为 `0`
- **AND** `truncated_count` MUST 为 `0`

#### Scenario: evidence snippets 超出预算时被裁剪或省略

- **WHEN** evidence snippets 的总字符数超过 `max_context_chars`
- **THEN** context budget MUST 按 retrieval 既有顺序纳入能放入预算的 evidence
- **AND** 超出预算的 evidence MUST 被裁剪或省略
- **AND** 预算摘要 MUST 记录 `omitted_count` 或 `truncated_count`
- **AND** `budget_used_chars` MUST NOT 大于 `max_context_chars`

### Requirement: Evidence Pack 审计不改变 chat 顶层 contract

系统 SHALL 将 Evidence Pack 摘要记录到内部 audit 或 trace 结构中。该摘要 MUST 使用固定 key：`evidence_items`、`included_count`、`omitted_count`、`truncated_count`、`budget_used_chars` 和 `max_context_chars`。

系统 MUST 保持 `/chat` 顶层响应 contract 不变，继续只要求 `trace_id`、`answer`、`related_files` 和 `tool_calls`。系统 MUST NOT 将完整 Evidence Pack 作为 `/chat` 必需顶层字段暴露。系统 MUST NOT 将完整 Evidence Pack 写入 `ToolExecutionResult.call_summary()` 或 `/chat.tool_calls`。

#### Scenario: chat 响应不暴露完整 evidence pack

- **WHEN** 用户通过 `/chat` 触发 repo search 并生成 Evidence Pack
- **THEN** `/chat` 响应 MUST 包含 `trace_id`、`answer`、`related_files` 和 `tool_calls`
- **AND** `/chat` 响应 MUST NOT 要求新的顶层 `evidence_pack` 字段
- **AND** `/chat.tool_calls` MUST NOT 包含完整 `evidence_pack`
- **AND** 内部 trace 或 audit summary MUST 记录固定 key 的 evidence pack 摘要

### Requirement: V10 不实现回答生成和未来检索能力

系统 SHALL 只实现 Evidence Pack 和 Context Budget 边界。系统 MUST NOT 在 V10 实现 grounded answer、model provider、LLM prompt assembly、LLM query rewrite、LLM rerank、memory、context compression、SandboxRunner、skill execution 或多 agent orchestration。

#### Scenario: 用户询问 V10 是否已经提供 grounded answer

- **WHEN** 用户询问当前是否已经实现 grounded answer、model provider、rerank、memory 或 context compression
- **THEN** 系统 MUST NOT 声称这些能力已在 V10 实现
- **AND** 系统 MAY 说明 V10 只提供 Evidence Pack 和 Context Budget 边界
- **AND** 系统 MUST NOT 执行不必要的 repo retrieval
