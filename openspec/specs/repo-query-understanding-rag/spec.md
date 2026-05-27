# repo-query-understanding-rag Specification

## Purpose

记录 V9-V12 已实现的检索前理解、deterministic query rewrite、repo-local lexical retrieval、轻量 embedding retrieval、hybrid fusion、before-Evidence rerank、Evidence Pack 和 Context Budget：系统在仓库检索前生成确定性 `SearchPlan`，对允许访问的 repo 文本文件生成轻量 chunk，通过 lexical 与本地 deterministic embedding 合并排序，并在 Evidence Pack 前执行 deterministic rerank，返回带相对路径和行号的 citation，并在成功 retrieval 后构建内部可审计 Evidence Pack。

RepoPilot adopts a grep-first, RAG-assisted retrieval stance: deterministic lexical/path/symbol search remains the primary auditable baseline, while embedding/hybrid retrieval is an auxiliary channel for semantic recall.

该能力不默认接入真实外部 embedding 服务、Milvus、Elasticsearch、PgVector、Qdrant、LLM query rewrite、LLM rerank、memory 或 context compression。Grounded answer 和 model provider 属于 `grounded-answer-model-provider` capability。

## Requirements

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

Hybrid fusion MUST 使用默认最低相关性阈值 `min_fused_score=0.35`。低于该阈值的 fused result MUST NOT 返回给 `/chat`。

系统 SHALL 记录 hybrid retrieval 的内部 channel audit summary。该 summary MUST 至少包含 retrieval mode、lexical result count、embedding result count、anchored embedding result count、fused result count 和 minimum fused score。该 summary MUST NOT 作为 `/chat` 顶层字段暴露。

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
- **AND** 当 lexical anchor 过滤 embedding-only 结果时，内部 trace SHOULD 记录 anchored embedding result count
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

### Requirement: 系统保持 chat contract 和只读检索边界

系统 SHALL 保持 `/chat` 顶层响应 contract 不变。系统 MUST 继续只返回 `trace_id`、`answer`、`related_files` 和 `tool_calls` 作为必需顶层字段。系统 MUST NOT 自动修改代码、执行 shell、执行 skill 或暴露内部 trace 为 `/chat` 顶层字段。

#### Scenario: hybrid retrieval 不新增 chat 顶层字段

- **WHEN** 用户通过 `/chat` 触发 repo search
- **THEN** 响应 MUST 包含 `trace_id`、`answer`、`related_files` 和 `tool_calls`
- **AND** 响应 MUST NOT 要求新的顶层字段
- **AND** `related_files` MUST 只包含相对 repo 路径

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
