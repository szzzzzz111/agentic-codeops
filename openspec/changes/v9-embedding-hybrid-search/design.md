## Context

RepoPilot 当前主链路是：

```text
API -> ChatService(trace_id) -> CodeAgent -> AgentLoop
  -> QueryUnderstanding/SearchPlan
  -> ToolRegistry -> PermissionPolicy -> ApprovalGate
  -> ToolExecutor(repo_rag) -> LexicalRepoRetriever -> file_tools
```

V8 已经实现 repo-local lexical RAG，并明确不实现 embedding、外部向量库、LLM rewrite、rerank、memory 或 context compression。这个边界适合作为 V8 收口，但从长期路线看，检索层下一步需要支持语义召回和 hybrid search。

V9 的关键是保持轻量工程化：先建立可替换接口和可测试闭环，不把项目拉进 Milvus/Elasticsearch/Qdrant 之类的重依赖。V9 仍然只做 retrieval，不做 answer generation。

## Goals / Non-Goals

**Goals:**

- 建立 `EmbeddingProvider` 边界，默认提供确定性轻量实现，便于测试和离线开发。
- 建立 repo-local embedding retrieval 通道，复用 V8 chunk 和 citation 约束。
- 保留 lexical retrieval，并通过 hybrid fusion 合并 lexical / embedding score。
- 让 `ToolExecutor(repo_rag)` 成为 V9 的 hybrid retrieval 审计入口。
- 保持 `/chat` 顶层 contract 不变。
- 把 V10 路线拆小，避免后续阶段一次承担 query rewrite、rerank、grounded answer 和 context budget。

**Non-Goals:**

- 不默认接入真实 embedding API、sentence-transformers、Milvus、Elasticsearch、PgVector、Qdrant 或 PostgreSQL。
- 不实现 LLM query rewrite、LLM rerank、grounded answer、model provider、memory、context compression、SandboxRunner、skill execution 或多 agent orchestration。
- 不新增 `/chat` 必需顶层字段。
- 不把参考项目写成 RepoPilot runtime dependency。

## Decisions

### Decision 1: 默认 embedding provider 使用确定性轻量实现

V9 默认实现应能在本地测试中稳定运行，不依赖网络、模型下载或外部服务。可以用 token hashing / character n-gram hashing 生成固定维度向量，目标不是语义效果生产可用，而是把 provider contract、embedding retrieval 和 hybrid fusion 打通。

替代方案：

- 直接接真实 embedding 服务：效果更接近真实，但引入网络、密钥、费用和测试不稳定性。
- 直接接 sentence-transformers：效果较好，但引入模型下载、环境体积和 CI 复杂度。

### Decision 2: lexical retrieval 保留为一等通道

V8 的 lexical scorer 对代码仓库很有价值，尤其是文件名、路径、符号和精确 token。V9 不用 embedding 替换 lexical，而是把 lexical 和 embedding 并列为 retrieval channels。

```text
SearchPlan
  -> LexicalRepoRetriever
  -> EmbeddingRepoRetriever
  -> HybridFusion
  -> citations / related_files / tool_calls
```

### Decision 3: embedding index 先做 repo-local in-memory

V9 可以在请求内或轻量对象生命周期内构建 embedding entries，不引入持久化索引。这样能先验证边界、排序和 audit 字段，避免提前设计缓存失效、增量更新和向量库 schema。

后续如果需要性能优化，可在单独阶段加入 SQLite/file cache 或外部向量后端。

### Decision 4: hybrid fusion 使用确定性归一化与加权

Fusion 应稳定、可测试、可解释。建议将 lexical score 和 embedding similarity 分别归一化，再按固定权重合成，并保留 path/symbol 命中对代码检索的优势。

V9 默认使用 `min_fused_score=0.5` 作为最低相关性阈值。低于该阈值的 fused result 不返回，避免轻量 deterministic embedding 把弱相关 chunk 捞进 `/chat` 结果。内部输出 score 可以继续使用整数摘要，但设计和测试按 `0.0-1.0` 的 fused score 理解阈值。

Hybrid retrieval SHOULD 记录内部 channel audit summary，至少包含 `mode=hybrid`、`lexical_results`、`embedding_results`、`fused_results` 和 `min_fused_score`。该摘要只进入内部 `trace_events_internal`，不新增 `/chat` 顶层字段。

V9 不做 LLM rerank。Rerank 留到后续阶段。

### Decision 5: 后续路线拆分

原 V10 范围过大，应拆为：

- V10: Evidence Pack + Context Budget
- V11: Grounded Answer / Model Provider Boundary
- V12: Query Rewrite + Rerank
- V13: Memory
- V14: Long Task / ReAct / Subagents
- V15: Personal Assistant Gateway

该路线拆分需要与 `README.md`、`docs/PROGRESS.md`、`docs/ARCHITECTURE.md` 和 `HANDOFF_TO_NEXT_CHAT.md` 保持一致；V9 规划阶段同步这些项目级文档，避免后续 review 口径冲突。

V9 的设计只为 V10 的 Evidence Pack 留数据结构上的可能性，不提前实现上下文预算或回答生成。

## Risks / Trade-offs

- [Risk] 轻量 deterministic embedding 效果不代表真实语义检索效果。 -> Mitigation: 明确这是默认测试实现，provider contract 保持可替换。
- [Risk] hybrid fusion 权重可能过早固定。 -> Mitigation: 先用小而明确的权重策略，并用测试覆盖路径/符号命中不被 embedding 淹没。
- [Risk] 请求内构建 embedding entries 对大仓库性能有限。 -> Mitigation: V9 聚焦边界和闭环，缓存/持久化索引留到后续阶段。
- [Risk] V9 可能滑向 V10/V11 的回答生成。 -> Mitigation: spec 和 review checklist 明确禁止 grounded answer、model provider、query rewrite 和 rerank。

## Migration Plan

1. 创建 V9 OpenSpec artifacts，并同步 `.harness/allowed_files.md` 与 `.harness/review_checklist.md`。
2. 先写失败测试，覆盖 embedding provider、embedding retrieval、hybrid fusion、`/chat` contract 和未实现能力状态。
3. 实现最小 provider/retriever/fusion 代码。
4. 更新 README、ARCHITECTURE、PROGRESS、FEATURE_LIST 和 HANDOFF。
5. 运行 `openspec validate v9-embedding-hybrid-search`、`powershell -ExecutionPolicy Bypass -File scripts/verify.ps1` 和 `git diff --check`。

Rollback 策略：V9 不引入外部服务或持久化迁移；如实现有问题，可回退到 V8 的 lexical-only `ToolExecutor(repo_rag)` 路径。

## Resolved Implementation Decisions

- V9 轻量 embedding provider 命名为 `DeterministicEmbeddingProvider`，强调本地、确定性、测试友好，而不是生产语义模型效果。
- Hybrid fusion 默认采用 lexical 优先权重：lexical `0.65` / embedding `0.35`。
- Hybrid fusion 默认使用 `min_fused_score=0.5` 过滤弱相关结果。
- Hybrid retrieval 记录内部 channel audit summary，并通过 `trace_events_internal` 暴露给 harness 内部审计，不新增 `/chat` 顶层字段。
