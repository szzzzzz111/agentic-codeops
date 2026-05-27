## Context

当前主链路是：

```text
API -> ChatService(trace_id) -> CodeAgent -> AgentLoop
  -> QueryUnderstanding/SearchPlan
  -> ToolRegistry -> PermissionPolicy -> ApprovalGate
  -> ToolExecutor(repo_rag) -> HybridRepoRetriever -> EvidencePack/ContextBudget
     -> GroundedAnswerGenerator -> ModelProvider
     -> LexicalRepoRetriever + EmbeddingRepoRetriever -> file_tools
```

V12 只增强 `repo_rag` 检索链路：在已有 `SearchPlan` 后做 bounded deterministic multi-query rewrite，在 Evidence Pack 前做 deterministic rerank。V12 不改变 API schema、权限/审批边界、安全文件工具、Evidence Pack budget 语义或 V11 citation validation。

## Goals / Non-Goals

**Goals:**

- 提供 `QueryRewriteProvider` 边界，默认 deterministic 实现。
- 支持 original query 加最多 3 条独立 Code Evidence query variants。
- 对 multi-query retrieval results 合并去重，并在 Evidence Pack 前执行 deterministic rerank。
- 保持 grep-first baseline：原始 query、path、symbol 和 exact token 直接命中具有稳定优先权。
- 在内部 trace/audit 中记录 rewrite/rerank provider、variant/result counts、status 和 fallback reason。
- 保持 `/chat` 顶层响应 contract 不变。

**Non-Goals:**

- 不默认调用真实 LLM、网络、API key 或真实模型输出。
- 不实现 LLM query rewrite、LLM rerank、memory、context compression、SandboxRunner、skill execution、多 agent 或 ReAct loop。
- 不引入 Milvus、Elasticsearch、PgVector、Qdrant、重型 embedding cache 或真实外部 embedding 服务。
- 不让 rewrite 改变 route、权限决策或整体 `question_type`。
- 不改变 Evidence Pack budget/summary 逻辑或 Grounded Answer citation validation 规则。

## Decisions

### Decision 1: Query rewrite 使用 bounded multi-query 容器

新增 `QueryVariant` 和 `QueryRewriteResult`。默认 provider 永远返回 `original` variant，并最多追加 3 条 deterministic Code Evidence variants。variant id 固定为 `original`、`definition`、`usage`、`configuration`、`tests`。

默认生成顺序固定为 `definition -> usage -> configuration -> tests`，按顺序截断到 `original + 3`。每个 variant 重新通过 QueryUnderstanding 构建自己的 terms，但继承 original plan 的 `question_type`、`max_results` 和 retrieval mode。

### Decision 2: Code Evidence variants 不主动扩展 docs/status

默认 deterministic provider 只围绕代码证据生成 variants：定义、调用/使用、配置和测试。它不主动生成 docs/progress/architecture/status variants，以避免把路线图、handoff 或历史归档文档误当成运行时证据。

### Decision 3: 去重和 fallback 必须稳定

variant 去重按归一化后的 `query_text`、`keywords`、`symbols` 和 `path_hints`。如果原始 plan 缺少可搜索 terms，则只保留 `original` variant，并记录 fallback reason。rewrite provider 异常时回退到只使用 original plan。

### Decision 4: Retrieval merge 保留原始 query 优先权

ToolExecutor 对每个 variant 执行现有 `HybridRepoRetriever.retrieve(...)`。合并时按 citation 去重，并保留命中来源：是否来自 original variant、variant ids 和最高 retrieval score。原始 query 的 path/symbol/exact token 直接命中在容量允许时不得被 variant-only 结果挤掉。

对包含 `symbols` 或 `path_hints` 的高精度查询，HybridRepoRetriever 保持 lexical anchor：embedding-only result 只能增强已有 lexical citation 命中，不能单独进入 fused pool。该规则不跳过任何 rewrite variant retrieval，只限制弱语义命中绕过 grep-first baseline。

### Decision 5: Rerank 只作用于 retrieval results 层

rerank 插在 merged retrieval pool 之后、Evidence Pack 之前。rerank 从 merged pool 中稳定选择最多 `SearchPlan.max_results` 条结果进入 Evidence Pack，不新增独立语义过滤阈值。rerank 失败时回退到未 rerank 的 merged results。

### Decision 6: Evidence Pack 和 Grounded Answer 语义不变

Evidence Pack 的 budget、summary、included/truncated/omitted 逻辑沿用 V10。V11 grounded answer 的 citation validation 仍只接受 included evidence；rerank 层之外的 citation 不得被视为合法回答 citation。

### Decision 7: Audit 仅内部记录

rewrite/rerank audit 只写入内部 `trace_events_internal`，例如 provider、variant_count、result counts、status 和 fallback reason。`/chat` 顶层字段和 `/chat.tool_calls` 摘要不暴露完整 variants、完整文件内容、完整 Evidence Pack、prompt、模型输出、API key 或本机绝对路径。

## Error Behavior

- rewrite 缺少可搜索 terms：只保留 original variant，记录 fallback reason。
- rewrite provider 异常：只使用 original plan。
- 单个 variant retrieval 失败：沿用当前 tool error 边界，返回 repo_rag error，不伪造 evidence。
- rerank provider 异常：回退到未 rerank merged results，继续构建 Evidence Pack。

## Rollback

V12 不做持久化迁移。若 rewrite/rerank 有问题，可回退到 V11 单 `SearchPlan` hybrid retrieval；`/chat` schema 无需迁移。
