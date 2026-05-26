## Context

RepoPilot 当前主链路是：

```text
API -> ChatService(trace_id) -> CodeAgent -> AgentLoop
  -> QueryUnderstanding/SearchPlan
  -> ToolRegistry -> PermissionPolicy -> ApprovalGate
  -> ToolExecutor(repo_rag) -> HybridRepoRetriever
     -> LexicalRepoRetriever + EmbeddingRepoRetriever -> file_tools
```

V9 已经提供 repo-local hybrid retrieval，并在内部 trace 记录 channel audit summary。当前缺口是 retrieval result 仍直接以 `file_path`、行号、`line_text` 和 score 的松散字典流向 AgentLoop，缺少一层“哪些证据可被后续回答使用、为什么被纳入、预算如何消耗”的稳定 contract。

V10 只建立证据整理和预算边界。它不负责生成最终自然语言答案，也不引入模型 provider；V11 再把 Evidence Pack 作为 grounded answer 的输入。

## Goals / Non-Goals

**Goals:**

- 定义结构化 `EvidenceItem` / `EvidencePack` / context budget report。
- 从 V9 `RetrievalResult` / `ToolExecutionResult` 构建稳定 evidence id、相对路径 citation、snippet、score 和来源摘要。
- 用 deterministic character budget 控制可用于后续上下文的 evidence snippets。
- 在内部 trace / audit summary 中记录 evidence pack 摘要，不改变 `/chat` 顶层 contract。
- 用测试覆盖 return shape、预算裁剪、路径安全、空结果、错误结果和非目标边界。

**Non-Goals:**

- 不实现 grounded answer、model provider、prompt template 或 LLM 调用。
- 不做 query rewrite、rerank、context compression、semantic chunk merge 或 token tokenizer 依赖。
- 不接 Memory、trace 持久化、SQLite/vector cache、外部向量库或外部 embedding 服务。
- 不新增 `/chat` 必需顶层字段。
- 不改变权限/审批策略，不绕过 `ToolExecutor(repo_rag)`。

## Decisions

### Decision 1: Evidence Pack 独立成轻量 RAG 子模块

V10 建议新增 `app/rag/evidence.py`，而不是继续把所有逻辑堆进 `repo_rag.py`。该模块只消费已通过安全文件边界的 retrieval dict 或 retrieval result，不直接读仓库、不调用文件工具、不做权限决策。

替代方案是把 pack builder 放进 `ToolExecutor`。这样改动更少，但会让执行入口同时承担数据建模、预算和审计整理，后续 V11 接 model provider 时边界会发黏。

### Decision 2: 默认预算用字符数而不是 tokenizer token

V10 使用 deterministic `max_context_chars=4000`。预算统计以 snippet 字符长度为准，必要时在字符边界裁剪最后一条可纳入 evidence，并记录 `budget_used_chars`、`budget_remaining_chars`、`included_count`、`omitted_count` 和 `truncated_count`。

替代方案是接真实 tokenizer。那会更接近模型上下文，但会引入 provider 差异、依赖和测试不稳定性。真实 token budget 可以留到 V11 model provider 边界或后续单独阶段。

### Decision 3: Evidence item 不返回本机绝对路径和完整文件内容

每个 evidence item 应只包含相对 `file_path`、`start_line`、`end_line`、短 snippet、score、source summary、稳定 `evidence_id`、`included` 和 `truncated`。V10 不读取完整文件内容，不把本机绝对路径写入 evidence pack 或 trace summary。

替代方案是保留更完整的 chunk text 供后续模型使用。当前阶段先保持安全、短上下文和可审计，避免把 V2/V8/V9 的文件读取边界冲散。

### Decision 4: `/chat` 顶层 contract 不变，Evidence Pack 只进入内部结构和审计

V10 在 `ToolExecutionResult` 上增加内部 `evidence_pack` 字段，并让 AgentLoop 内部 trace 记录 `evidence_pack_summarized` 摘要。`/chat` 顶层仍只返回 `trace_id`、`answer`、`related_files`、`tool_calls`；`ToolExecutionResult.evidence_pack` MUST NOT 进入 `call_summary()`、`tool_calls` 或 `/chat` 顶层响应。

替代方案是在 `/chat` 顶层返回 `evidence_pack`。这会让 API contract 提前绑定 V11 之前的内部结构，且与当前阶段“不做回答生成，只准备边界”的目标不匹配。

### Decision 5: trace/audit 固定只记录 Evidence Pack 摘要

V10 的完整 Evidence Pack 留在内部 `ToolExecutionResult.evidence_pack`，trace/audit 只记录固定 summary keys：`evidence_items`、`included_count`、`omitted_count`、`truncated_count`、`budget_used_chars` 和 `max_context_chars`。Trace 不记录完整 snippets。

### Decision 6: Evidence Pack 不改变 retrieval 排序语义

Evidence Pack builder 按 retriever 已给出的稳定顺序消费结果，只负责预算纳入和审计摘要，不重新排序、不 rerank、不合并语义相近 chunk。V12 再处理 query rewrite / rerank。

## Risks / Trade-offs

- [Risk] 字符预算不是模型真实 token 预算。 -> Mitigation: 字段命名明确为 `max_context_chars` / `budget_used_chars`，V11 再决定是否映射到 provider token budget。
- [Risk] Evidence Pack 可能被误解为已生成 grounded answer。 -> Mitigation: spec、docs 和 review checklist 明确 V10 不做 answer generation 或 model provider。
- [Risk] 把 snippets 放进内部结构会扩大 trace 内容。 -> Mitigation: 限制 snippet 长度，只记录相对路径和短文本，不持久化，不作为 `/chat` 顶层字段。
- [Risk] V10 可能滑向 rerank 或 compression。 -> Mitigation: Pack builder 保持输入顺序，只做 include / omit / truncate。

## Completed Implementation Notes

1. 已同步 V10 OpenSpec artifacts 和 `.harness` 边界，并在 plan/review 确认后进入实现。
2. 已补充测试覆盖 evidence item shape、context budget 和 `/chat` contract。
3. 已新增 `app/rag/evidence.py` 并接入 `ToolExecutor.search_repo_rag` 的内部结果。
4. 已在 AgentLoop trace 中记录 evidence pack summary，保持 `/chat` 顶层 contract 不变。
5. 已更新 README、ARCHITECTURE、PROGRESS、FEATURE_LIST 和 HANDOFF。
6. 已运行 `openspec validate v10-evidence-pack-context-budget`、`powershell -ExecutionPolicy Bypass -File scripts/verify.ps1` 和 `git diff --check`。

Rollback 策略：V10 不引入外部依赖或持久化迁移；如实现有问题，可回退到 V9 的 `ToolExecutor(repo_rag) -> HybridRepoRetriever` 结果路径。

## Resolved Implementation Decisions

- V10 默认 `max_context_chars=4000`。
- 完整 Evidence Pack 保留在内部 `ToolExecutionResult.evidence_pack`。
- `call_summary()`、`tool_calls` 和 `/chat` 顶层响应不暴露完整 Evidence Pack。
- 内部 trace/audit 只记录固定 Evidence Pack summary keys，不记录完整 snippets。
