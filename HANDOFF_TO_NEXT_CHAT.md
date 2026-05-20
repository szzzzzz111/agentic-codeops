# 交接给下一轮 Chat

## 当前状态

```text
当前工作分支：main
当前基线分支：main
当前活跃 OpenSpec change：无
最近完成阶段：V8 Query Understanding + Lexical Repo RAG
```

RepoPilot 当前定位为面向代码仓库分析任务的可控 Code Agent Harness，不是替代通用 AI IDE 的编程助手。V1-V8 已完成并进入长期规格/归档历史；当前暂无活跃 OpenSpec change。

V8 已归档到：

```text
openspec/changes/archive/2026-05-20-v8-query-understanding-repo-rag/
```

## 当前主链路

```text
API -> ChatService(trace_id) -> CodeAgent -> AgentLoop
  -> QueryUnderstanding/SearchPlan
  -> ToolRegistry -> PermissionPolicy -> ApprovalGate
  -> ToolExecutor(repo_rag) -> LexicalRepoRetriever -> file_tools
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
- 已将 `/chat` 的 repo_search 分支从简单 `search_code` 搜索升级为 `ToolExecutor(repo_rag) -> LexicalRepoRetriever`。
- 已同步长期 specs：
  - `openspec/specs/agent-loop-tool-execution/spec.md`
  - `openspec/specs/repo-query-understanding-rag/spec.md`

V8 不实现 embedding、Milvus、Elasticsearch、PgVector、Qdrant、LLM rewrite、rerank、memory、SandboxRunner、skill execution 或多 agent orchestration。

## 当前 Harness 状态

- `.harness/allowed_files.md` 已切回无活跃阶段。
- `.harness/review_checklist.md` 已切回无活跃阶段。
- `openspec list` 应显示 `No active changes found`。
- 新阶段开始前必须先创建 OpenSpec change，并同步 `.harness/allowed_files.md` 和 `.harness/review_checklist.md`。

## 下一轮建议

1. 规划 V9：Embedding Retrieval + Hybrid Search。
2. V9 优先做 embedding provider 接口、轻量默认实现、hybrid fusion 和可替换后端边界。
3. V9 保留 V8 lexical repo RAG 作为一等通道。
4. Milvus / Elasticsearch 暂不默认引入，先写成可替换后端或后续选项。
5. 不要把 query rewrite、rerank、memory、long task 或 subagents 提前塞进 V9。

后续路线建议：V10 做 Query Rewrite / Rerank / Grounded Answer / Context Budget；V11 做 Memory；V12 做 Long Task / ReAct / Subagents；V13 做 Personal Assistant Gateway。
