## MODIFIED Requirements

### Requirement: 系统执行确定性 Context Budget

系统 SHALL 对 Evidence Pack 执行确定性 context budget。Context budget MUST 使用字符预算边界，默认 `max_context_chars` MUST 为稳定常量，并且 MUST 记录 `budget_used_chars`、`budget_remaining_chars`、`included_count`、`omitted_count` 和 `truncated_count`。

系统 MUST 按 retrieval 既有稳定排序纳入 evidence items。系统 MUST NOT 在 context budget 阶段执行 LLM rerank、query rewrite、context compression 或语义合并。

空或仅空白的 evidence snippet 在 normalized snippet 为空后 MUST 保留 evidence item 以便审计，但 MUST NOT 计入 `included_count`，MUST NOT 消耗 context budget，MUST NOT 标记为 `truncated`，并 MUST 计入 `omitted_count`。

#### Scenario: non-empty evidence snippets 在预算内全部纳入

- **WHEN** retrieval results contain no empty or whitespace-only snippets
- **AND** evidence snippets 的总字符数不超过 `max_context_chars`
- **THEN** context budget MUST 纳入全部非空 evidence items
- **AND** `omitted_count` MUST 为 `0`
- **AND** `truncated_count` MUST 为 `0`

#### Scenario: evidence snippets 超出预算时被裁剪或省略

- **WHEN** evidence snippets 的总字符数超过 `max_context_chars`
- **THEN** context budget MUST 按 retrieval 既有顺序纳入能放入预算的 evidence
- **AND** 超出预算的 evidence MUST 被裁剪或省略
- **AND** 预算摘要 MUST 记录 `omitted_count` 或 `truncated_count`
- **AND** `budget_used_chars` MUST NOT 大于 `max_context_chars`

#### Scenario: empty snippet is omitted without consuming budget

- **WHEN** a retrieval result has an empty or whitespace-only snippet after normalization
- **THEN** the Evidence Pack keeps the evidence item with `included=False`
- **AND** the item is not marked `truncated`
- **AND** context budget does not count the item as included
- **AND** context budget records the item as omitted without consuming characters
