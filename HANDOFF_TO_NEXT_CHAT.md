# 交接给下一轮 Chat

## 当前状态

```text
当前工作分支：codex/v9-embedding-hybrid-search
当前基线分支：main
当前活跃 OpenSpec change：v9-embedding-hybrid-search
最近完成阶段：V8 Query Understanding + Lexical Repo RAG
```

RepoPilot 当前定位为面向代码仓库分析任务的可控 Code Agent Harness，不是替代通用 AI IDE 的编程助手。V1-V8 已完成并进入长期规格/归档历史；当前 V9 `v9-embedding-hybrid-search` 已实现运行时代码，正在进行最终验证与收口。

V8 已归档到：

```text
openspec/changes/archive/2026-05-20-v8-query-understanding-repo-rag/
```

## 当前主链路

```text
API -> ChatService(trace_id) -> CodeAgent -> AgentLoop
  -> QueryUnderstanding/SearchPlan
  -> ToolRegistry -> PermissionPolicy -> ApprovalGate
  -> ToolExecutor(repo_rag) -> HybridRepoRetriever
     -> LexicalRepoRetriever + EmbeddingRepoRetriever -> file_tools
```

`/chat` 顶层响应保持现有 contract：`trace_id`、`answer`、`related_files`、`tool_calls`。V7 的权限和审批审计、V8 的 query understanding/retrieval 摘要只保留在内部 `trace_events_internal`，不作为 `/chat` 顶层字段暴露。

## 已完成阶段摘要

### V7：Permission + Approval Gate

- 已提交：`7f1fc86 Add V7 permission approval gate`
- 已合并到 `main`：`Merge V7 permission approval gate`
- 已归档到：`openspec/changes/archive/2026-05-19-v7-permission-approval-gate/`
- 已实现 `ToolSpec.requires_approval`、`PermissionDecision`、`PermissionPolicy` 和最小 `ApprovalGate`。
- 权限优先级：未注册、非只读或非 `low` 风险 -> `deny`；否则 `requires_approval=True` -> `ask`；否则 -> `allow`。
- `deny` 和 `ask` 分支不调用 executor，`related_files=[]` 且 `tool_calls=[]`。

### V8：Query Understanding + Lexical Repo RAG

- 已提交：`2ab1316 Add V8 query understanding repo RAG`
- 已合并到 `main`：`cef8115 Merge V8 query understanding repo RAG`
- 已归档：`eff51c3 Archive V8 query understanding repo RAG`
- 已新增 deterministic `QueryUnderstanding/SearchPlan`。
- 已新增 repo-local lexical RAG：repo chunk、lexical scoring、dedup 和 citation。
- 已将 `/chat` 的 repo_search 分支从简单 `search_code` 搜索升级为 V8 的 `ToolExecutor(repo_rag) -> LexicalRepoRetriever`；当前 V9 分支已进一步升级为 `HybridRepoRetriever`。
- 已同步长期 specs：
  - `openspec/specs/agent-loop-tool-execution/spec.md`
  - `openspec/specs/repo-query-understanding-rag/spec.md`

V8 不实现 embedding、Milvus、Elasticsearch、PgVector、Qdrant、LLM rewrite、rerank、memory、SandboxRunner、skill execution 或多 agent orchestration。

## 当前 Harness 状态

- `.harness/allowed_files.md` 已切换到 V9 允许修改范围。
- `.harness/review_checklist.md` 已切换到 V9 review 清单。
- `openspec/changes/v9-embedding-hybrid-search/` 已创建 proposal、design、spec delta 和 tasks。
- `openspec validate v9-embedding-hybrid-search` 已通过。
- 当前已实现 V9 运行时代码，并完成全量验证；尚需归档前 review 和 OpenSpec archive。
- V9 验证结果：
  - `openspec validate v9-embedding-hybrid-search`：通过
  - `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`：通过；`pytest` 66 passed, 1 skipped；`ruff check .` All checks passed
  - `git diff --check`：通过，仅有 CRLF 换行提示

## 下一轮建议

1. 做归档前 review，确认没有把 Milvus / Elasticsearch / PgVector / Qdrant、query rewrite、rerank、grounded answer、model provider、memory、long task 或 subagents 提前塞进 V9。
2. 如 review 通过，归档 `v9-embedding-hybrid-search` 并同步长期 spec。

后续路线已拆分：V10 做 Evidence Pack + Context Budget；V11 做 Grounded Answer / Model Provider Boundary；V12 做 Query Rewrite + Rerank；V13 做 Memory；V14 做 Long Task / ReAct / Subagents；V15 做 Personal Assistant Gateway。
