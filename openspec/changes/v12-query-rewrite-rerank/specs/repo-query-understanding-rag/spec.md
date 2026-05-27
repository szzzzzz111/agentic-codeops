# repo-query-understanding-rag Specification

## MODIFIED Requirements

### Requirement: 系统执行确定性 Query Understanding

系统 SHALL 在 repo-local 检索前执行确定性 Query Understanding。Query Understanding MUST NOT 调用 LLM、embedding provider、向量库或外部服务。

Query Understanding MUST 产生 `SearchPlan`，至少包含问题类型、关键词、符号、路径提示、最大结果数和 retrieval mode。问题类型 MUST 至少覆盖代码定位、实现解释、调用关系、测试/验证、文件摘要和未知泛问。

系统 SHALL 在 `SearchPlan` 后执行 deterministic query rewrite。默认 rewrite provider MUST NOT 调用 LLM、网络、API key 或外部服务。rewrite MUST 保留 original query variant，并 MAY 生成最多 3 条独立 Code Evidence query variants。

#### Scenario: 从代码问题中提取检索计划

- **WHEN** 用户消息包含文件名、路径片段、函数名、类名、错误词或普通代码问题
- **THEN** 系统生成包含 `question_type`、`keywords`、`symbols`、`path_hints`、`max_results` 和 `retrieval_mode` 的 `SearchPlan`
- **AND** `retrieval_mode` SHOULD 为 `hybrid`

#### Scenario: deterministic rewrite 生成稳定 query variants

- **WHEN** original `SearchPlan` 包含可搜索 terms
- **THEN** rewrite result MUST 包含 `original` variant
- **AND** rewrite result MAY 按 `definition`、`usage`、`configuration`、`tests` 顺序生成最多 3 条额外 variants
- **AND** variant ids MUST 稳定
- **AND** rewrite MUST NOT 改变 route、权限决策或整体 `question_type`

#### Scenario: 缺少可搜索 terms 时 rewrite 降级

- **WHEN** original `SearchPlan` 不包含可搜索 terms
- **THEN** rewrite result MUST 只包含 `original` variant
- **AND** audit summary MUST 记录 fallback reason

### Requirement: 系统执行 hybrid retrieval fusion

系统 SHALL 保留 lexical retrieval 和 embedding retrieval 两个一等通道，并通过 deterministic hybrid fusion 合并排序结果。Fusion MUST 保持稳定排序，并且 MUST 保留路径、文件名、符号和 exact token 命中的权重优势。

Hybrid fusion MUST 使用默认最低相关性阈值 `min_fused_score=0.35`。低于该阈值的 fused result MUST NOT 返回给 `/chat`。

系统 SHALL 记录 hybrid retrieval 的内部 channel audit summary。该 summary MUST 至少包含 retrieval mode、lexical result count、embedding result count、fused result count 和 minimum fused score。该 summary MUST NOT 作为 `/chat` 顶层字段暴露。

当 `SearchPlan` 包含 `symbols` 或 `path_hints` 时，hybrid retrieval MUST 保持 lexical anchor：未与 lexical result citation 重合的 embedding-only result MUST NOT 独立进入 fused pool。

V12 SHALL 对 rewrite variants 执行 bounded multi-query retrieval，并在 Evidence Pack 前执行 deterministic rerank。Rerank MUST 只作用于 retrieval results 层，MUST 从 merged retrieval pool 中稳定选择最多 `SearchPlan.max_results` 条结果进入 Evidence Pack，并且 MUST NOT 新增独立语义过滤阈值。

#### Scenario: lexical 和 embedding 命中被合并去重

- **WHEN** lexical retrieval 和 embedding retrieval 返回同一个 chunk
- **THEN** hybrid fusion MUST 合并该 chunk 的分数
- **AND** 最终结果中该 chunk MUST 只出现一次
- **AND** 最终排序 MUST 稳定

#### Scenario: 直接路径或符号命中不被 embedding 淹没

- **WHEN** 一个 chunk 直接命中用户问题中的路径或符号，而另一个 chunk 只有 embedding 相似
- **THEN** hybrid fusion MUST 让直接路径或符号命中的 chunk 排在更靠前的位置

#### Scenario: 符号或路径查询需要 lexical anchor

- **WHEN** `SearchPlan` 包含 `symbols` 或 `path_hints`
- **AND** embedding retrieval 返回的 chunk 没有对应 lexical citation 命中
- **THEN** 该 embedding-only chunk MUST NOT 独立进入 fused pool
- **AND** rewrite variants MUST 仍被执行，不得因 original variant 为空而整体跳过

#### Scenario: 低于最低相关性阈值的结果不返回

- **WHEN** 一个 fused result 的相关性低于 `min_fused_score=0.35`
- **THEN** hybrid fusion MUST NOT 返回该 result

#### Scenario: hybrid 检索记录通道审计摘要

- **WHEN** 系统执行 hybrid retrieval
- **THEN** 内部 trace MUST 记录 lexical、embedding 和 fused result count
- **AND** 内部 trace MUST 记录 `min_fused_score=0.35`
- **AND** `/chat` 顶层响应 MUST NOT 新增审计字段

#### Scenario: multi-query retrieval 保留 original 优先权

- **WHEN** original variant 和 rewrite-only variant 都返回结果
- **THEN** 系统 MUST 合并并去重 retrieval results
- **AND** original variant 的 path、symbol 或 exact token 直接命中在容量允许时 MUST NOT 被 rewrite-only 结果挤掉

#### Scenario: rerank 不改变 Evidence Pack 语义

- **WHEN** rerank 选择 retrieval results 进入 Evidence Pack
- **THEN** Evidence Pack budget、summary、included、truncated 和 omitted 逻辑 MUST 保持既有语义
- **AND** grounded answer citation validation MUST 仍只接受 included evidence

### Requirement: 系统不默认引入重型检索基础设施

系统 SHALL 采用 grep-first, RAG-assisted 检索立场：deterministic lexical search、path search、symbol search 和 exact token match MUST 作为主要可审计检索基线保留。Embedding retrieval、hybrid retrieval、query rewrite 和 rerank MUST 只作为辅助召回或排序通道，不得替代 grep-like baseline。

系统 SHALL 引入轻量 embedding retrieval、hybrid search、deterministic query rewrite 和 deterministic rerank。系统 MUST NOT 默认引入 Milvus、Elasticsearch、PgVector、Qdrant、真实外部 embedding 服务、重型 embedding cache、LLM query rewrite、LLM rerank 或 memory。关键词、符号、路径和文件名检索 MUST 作为一等检索通道保留。

#### Scenario: 用户询问未默认引入的重型检索能力

- **WHEN** 用户询问当前是否默认接入 Milvus、Elasticsearch、PgVector、Qdrant、真实外部 embedding 服务、重型 embedding cache 或 memory
- **THEN** 系统回答 MUST NOT 声称这些能力已默认接入
- **AND** 系统 MAY 说明当前检索采用 grep-first, RAG-assisted 立场，embedding/hybrid retrieval 只是辅助通道
- **AND** 系统 MUST NOT 执行不必要的 repo retrieval
- **AND** `related_files` 和 `tool_calls` 均为空列表

#### Scenario: rewrite 和 rerank 服务于 grep-first baseline

- **WHEN** 系统执行 query rewrite 或 rerank
- **THEN** query rewrite 和 rerank MUST 服务于 deterministic lexical/path/symbol 检索基线
- **AND** 系统 MUST NOT 因 query rewrite 或 rerank 默认切换为向量库优先检索
- **AND** 系统 MUST NOT 默认调用真实 LLM rewrite 或 LLM rerank
