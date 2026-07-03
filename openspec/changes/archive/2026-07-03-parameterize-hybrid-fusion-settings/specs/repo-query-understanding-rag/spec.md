## MODIFIED Requirements

### Requirement: 系统执行 hybrid retrieval fusion

系统 SHALL 保留 lexical retrieval 和 embedding retrieval 两个一等通道，并通过 deterministic hybrid fusion 合并排序结果。Fusion MUST 保持稳定排序，并且 MUST 保留路径、文件名、符号和 exact token 命中的权重优势。

Hybrid fusion MUST 使用显式 deterministic fusion settings，默认设置 MUST 保持 `lexical_weight=0.65`、`embedding_weight=0.35` 和 `min_fused_score=0.35`。系统 MUST 校验 fusion weights 和 minimum fused score，拒绝负数、非有限数值或全零权重。低于 effective `min_fused_score` 的 fused result MUST NOT 返回给 `/chat`。

系统 SHALL 记录 hybrid retrieval 的内部 channel audit summary。该 summary MUST 至少包含 retrieval mode、lexical result count、embedding result count、anchored embedding result count、fused result count、effective lexical weight、effective embedding weight 和 effective minimum fused score。该 summary MUST NOT 作为 `/chat` 顶层字段暴露。

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

- **WHEN** 一个 fused result 的相关性低于 effective `min_fused_score`
- **THEN** hybrid fusion MUST NOT 返回该 result

#### Scenario: hybrid 检索记录通道审计摘要

- **WHEN** 系统执行 hybrid retrieval
- **THEN** 内部 trace MUST 记录 lexical、embedding 和 fused result count
- **AND** 当 lexical anchor 过滤 embedding-only 结果时，内部 trace SHOULD 记录 anchored embedding result count
- **AND** 内部 trace MUST 记录 effective `lexical_weight`、`embedding_weight` 和 `min_fused_score`
- **AND** `/chat` 顶层响应 MUST NOT 新增审计字段

#### Scenario: invalid fusion settings fail closed

- **WHEN** hybrid fusion settings contain a negative value, non-finite value, or all-zero weights
- **THEN** the system MUST reject those settings before scoring
- **AND** the default fusion behavior MUST remain unchanged

#### Scenario: multi-query retrieval 保留 original 优先权

- **WHEN** original variant 和 rewrite-only variant 都返回结果
- **THEN** 系统 MUST 合并并去重 retrieval results
- **AND** original variant 的 path、symbol 或 exact token 直接命中在容量允许时 MUST NOT 被 rewrite-only 结果挤掉

#### Scenario: rerank 不改变 Evidence Pack 语义

- **WHEN** rerank 选择 retrieval results 进入 Evidence Pack
- **THEN** Evidence Pack budget、summary、included、truncated 和 omitted 逻辑 MUST 保持既有语义
- **AND** grounded answer citation validation MUST 仍只接受 included evidence
