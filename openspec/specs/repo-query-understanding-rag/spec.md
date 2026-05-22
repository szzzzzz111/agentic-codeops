# repo-query-understanding-rag Specification

## Purpose

记录 V9 已实现的检索前理解、repo-local lexical retrieval、轻量 embedding retrieval 和 hybrid fusion：系统在仓库检索前生成确定性 `SearchPlan`，对允许访问的 repo 文本文件生成轻量 chunk，并通过 lexical 与本地 deterministic embedding 两个一等通道合并排序，返回带相对路径和行号的 citation。

该能力不默认接入真实外部 embedding 服务、Milvus、Elasticsearch、PgVector、Qdrant、LLM query rewrite、LLM rerank、grounded answer、model provider 或 memory。

## Requirements

### Requirement: 系统执行确定性 Query Understanding

系统 SHALL 在 repo-local 检索前执行确定性 Query Understanding。Query Understanding MUST NOT 调用 LLM、embedding provider、向量库或外部服务。

Query Understanding MUST 产生 `SearchPlan`，至少包含问题类型、关键词、符号、路径提示、最大结果数和 retrieval mode。问题类型 MUST 至少覆盖代码定位、实现解释、调用关系、测试/验证、文件摘要和未知泛问。

#### Scenario: 从代码问题中提取检索计划

- **WHEN** 用户消息包含文件名、路径片段、函数名、类名、错误词或普通代码问题
- **THEN** 系统生成包含 `question_type`、`keywords`、`symbols`、`path_hints`、`max_results` 和 `retrieval_mode` 的 `SearchPlan`
- **AND** `retrieval_mode` SHOULD 为 `hybrid`

### Requirement: 系统执行 repo-local lexical chunk retrieval

系统 SHALL 对 repo 内允许访问的文本文件生成轻量 chunk，并使用 lexical scorer 检索相关 chunk。每个 chunk MUST 包含 `chunk_id`、`file_path`、`start_line`、`end_line` 和 `text`。

Lexical scorer MUST 至少考虑 keyword match、symbol match、path match、filename match 和 exact token bonus。检索结果 MUST 带 citation，citation MUST 使用相对 repo 路径和 1-based 行号。

#### Scenario: 符号和路径命中排在普通关键词前

- **WHEN** repo 中存在多个包含普通关键词的文件，并且其中一个文件路径或符号直接命中用户问题
- **THEN** 直接命中的 chunk 排序 SHOULD 高于只有普通关键词命中的 chunk
- **AND** citation MUST 包含相对 `file_path`、`start_line` 和 `end_line`

### Requirement: 系统提供可替换 embedding provider 边界

系统 SHALL 提供 embedding provider 边界，用于把查询文本和 repo chunk 文本转换为固定维度向量。默认 provider MUST 是本地确定性实现，并且 MUST NOT 依赖网络、密钥、模型下载或外部服务。

#### Scenario: 默认 provider 稳定生成向量

- **WHEN** 系统使用默认 embedding provider 对相同文本生成向量
- **THEN** 返回的向量 MUST 稳定一致
- **AND** 向量维度 MUST 固定
- **AND** provider MUST NOT 调用外部服务

### Requirement: 系统执行 repo-local embedding retrieval

系统 SHALL 在安全文件边界内对允许访问的 repo 文本 chunk 执行 embedding retrieval。Embedding retrieval MUST 复用相对 repo 路径、1-based 行号和 citation 约束，并且 MUST NOT 返回本机绝对路径。

#### Scenario: embedding retrieval 返回带 citation 的结果

- **WHEN** 用户问题与某个 repo chunk 语义向量相近
- **THEN** embedding retrieval 返回该 chunk 的 citation
- **AND** citation MUST 包含相对 `file_path`、`start_line` 和 `end_line`
- **AND** citation MUST NOT 包含本机绝对路径

### Requirement: 系统执行 hybrid retrieval fusion

系统 SHALL 保留 lexical retrieval 和 embedding retrieval 两个一等通道，并通过 deterministic hybrid fusion 合并排序结果。Fusion MUST 保持稳定排序，并且 MUST 保留路径、文件名、符号和 exact token 命中的权重优势。

Hybrid fusion MUST 使用默认最低相关性阈值 `min_fused_score=0.5`。低于该阈值的 fused result MUST NOT 返回给 `/chat`。

系统 SHALL 记录 hybrid retrieval 的内部 channel audit summary。该 summary MUST 至少包含 retrieval mode、lexical result count、embedding result count、fused result count 和 minimum fused score。该 summary MUST NOT 作为 `/chat` 顶层字段暴露。

#### Scenario: lexical 和 embedding 命中被合并去重

- **WHEN** lexical retrieval 和 embedding retrieval 返回同一个 chunk
- **THEN** hybrid fusion MUST 合并该 chunk 的分数
- **AND** 最终结果中该 chunk MUST 只出现一次
- **AND** 最终排序 MUST 稳定

#### Scenario: 直接路径或符号命中不被 embedding 淹没

- **WHEN** 一个 chunk 直接命中用户问题中的路径或符号，而另一个 chunk 只有 embedding 相似
- **THEN** hybrid fusion MUST 让直接路径或符号命中的 chunk 排在更靠前的位置

#### Scenario: 低于最低相关性阈值的结果不返回

- **WHEN** 一个 fused result 的相关性低于 `min_fused_score=0.5`
- **THEN** hybrid fusion MUST NOT 返回该 result

#### Scenario: hybrid 检索记录通道审计摘要

- **WHEN** 系统执行 hybrid retrieval
- **THEN** 内部 trace MUST 记录 lexical、embedding 和 fused result count
- **AND** 内部 trace MUST 记录 `min_fused_score=0.5`
- **AND** `/chat` 顶层响应 MUST NOT 新增审计字段

### Requirement: 系统保持 chat contract 和只读检索边界

系统 SHALL 保持 `/chat` 顶层响应 contract 不变。系统 MUST 继续只返回 `trace_id`、`answer`、`related_files` 和 `tool_calls` 作为必需顶层字段。系统 MUST NOT 自动修改代码、执行 shell、执行 skill 或暴露内部 trace 为 `/chat` 顶层字段。

#### Scenario: hybrid retrieval 不新增 chat 顶层字段

- **WHEN** 用户通过 `/chat` 触发 repo search
- **THEN** 响应 MUST 包含 `trace_id`、`answer`、`related_files` 和 `tool_calls`
- **AND** 响应 MUST NOT 要求新的顶层字段
- **AND** `related_files` MUST 只包含相对 repo 路径

### Requirement: 系统不默认引入重型检索基础设施

系统 SHALL 引入轻量 embedding retrieval 和 hybrid search。系统 MUST NOT 默认引入 Milvus、Elasticsearch、PgVector、Qdrant、真实外部 embedding 服务、LLM query rewrite、LLM rerank 或 memory。关键词、符号、路径和文件名检索 MUST 作为一等检索通道保留。

#### Scenario: 用户询问未默认引入的重型检索能力

- **WHEN** 用户询问当前是否默认接入 Milvus、Elasticsearch、PgVector、Qdrant、真实外部 embedding 服务或 memory
- **THEN** 系统回答 MUST NOT 声称这些能力已默认接入
- **AND** 系统 MAY 说明 V9 提供轻量 embedding retrieval 和 hybrid search
- **AND** 系统 MUST NOT 执行不必要的 repo retrieval
- **AND** `related_files` 和 `tool_calls` 均为空列表
