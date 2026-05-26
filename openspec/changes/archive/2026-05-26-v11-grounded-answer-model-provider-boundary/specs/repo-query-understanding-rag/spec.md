# repo-query-understanding-rag Specification

## MODIFIED Requirements

### Requirement: 系统不默认引入重型检索基础设施

系统 SHALL 采用 grep-first, RAG-assisted 检索立场：deterministic lexical search、path search、symbol search 和 exact token match MUST 作为主要可审计检索基线保留。Embedding retrieval、hybrid retrieval、query rewrite 和 rerank MUST 只作为辅助召回或排序通道，不得替代 grep-like baseline。

系统 SHALL 引入轻量 embedding retrieval 和 hybrid search。系统 MUST NOT 默认引入 Milvus、Elasticsearch、PgVector、Qdrant、真实外部 embedding 服务、重型 embedding cache、LLM query rewrite、LLM rerank 或 memory。关键词、符号、路径和文件名检索 MUST 作为一等检索通道保留。

#### Scenario: 用户询问未默认引入的重型检索能力

- **WHEN** 用户询问当前是否默认接入 Milvus、Elasticsearch、PgVector、Qdrant、真实外部 embedding 服务、重型 embedding cache 或 memory
- **THEN** 系统回答 MUST NOT 声称这些能力已默认接入
- **AND** 系统 MAY 说明当前检索采用 grep-first, RAG-assisted 立场，embedding/hybrid retrieval 只是辅助通道
- **AND** 系统 MUST NOT 执行不必要的 repo retrieval
- **AND** `related_files` 和 `tool_calls` 均为空列表

#### Scenario: 后续 rewrite 和 rerank 服务于 grep-first baseline

- **WHEN** 后续阶段引入 query rewrite 或 rerank
- **THEN** query rewrite 和 rerank MUST 服务于 deterministic lexical/path/symbol 检索基线
- **AND** 系统 MUST NOT 因 query rewrite 或 rerank 默认切换为向量库优先检索
