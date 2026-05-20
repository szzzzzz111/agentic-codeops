# repo-query-understanding-rag Delta

## ADDED Requirements

### Requirement: 系统执行确定性 Query Understanding

系统 SHALL 在 repo-local 检索前执行确定性 Query Understanding。Query Understanding MUST NOT 调用 LLM、embedding provider、向量库或外部服务。

Query Understanding MUST 产生 `SearchPlan`，至少包含问题类型、关键词、符号、路径提示和最大结果数。问题类型 MUST 至少覆盖代码定位、实现解释、调用关系、测试/验证、文件摘要和未知泛问。

#### Scenario: 从代码问题中提取检索计划

- **WHEN** 用户消息包含文件名、路径片段、函数名、类名、错误词或普通代码问题
- **THEN** 系统生成包含 `question_type`、`keywords`、`symbols`、`path_hints` 和 `max_results` 的 `SearchPlan`
- **AND** 系统 MUST NOT 把该计划标记为 embedding 或 vector 检索

### Requirement: 系统执行 repo-local lexical chunk retrieval

系统 SHALL 对 repo 内允许访问的文本文件生成轻量 chunk，并使用 lexical scorer 检索相关 chunk。每个 chunk MUST 包含 `chunk_id`、`file_path`、`start_line`、`end_line` 和 `text`。

Lexical scorer MUST 至少考虑 keyword match、symbol match、path match、filename match 和 exact token bonus。检索结果 MUST 带 citation，citation MUST 使用相对 repo 路径和 1-based 行号。

#### Scenario: 符号和路径命中排在普通关键词前

- **WHEN** repo 中存在多个包含普通关键词的文件，并且其中一个文件路径或符号直接命中用户问题
- **THEN** 直接命中的 chunk 排序 SHOULD 高于只有普通关键词命中的 chunk
- **AND** citation MUST 包含相对 `file_path`、`start_line` 和 `end_line`

### Requirement: V8 不实现向量化或重型检索基础设施

V8 MUST NOT 实现 embedding、Milvus、Elasticsearch、PgVector、Qdrant、LLM query rewrite、LLM rerank 或 memory。关键词/符号/路径检索 MUST 作为当前阶段的一等检索通道保留。

#### Scenario: 用户询问未实现的向量能力

- **WHEN** 用户询问当前是否实现 embedding、Milvus、Elasticsearch、PgVector 或 memory
- **THEN** 系统回答 MUST NOT 声称这些能力已实现
- **AND** 系统 MAY 说明当前 V8 只提供 lexical repo RAG
- **AND** 系统 MUST NOT 执行 repo retrieval
- **AND** `related_files` 和 `tool_calls` 均为空列表
