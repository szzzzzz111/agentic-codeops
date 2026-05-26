# 交接给下一轮 Chat

## 当前状态

```text
当前工作分支：feature/v11-grounded-answer-model-provider-boundary
当前基线分支：main
当前活跃 OpenSpec change：无
最近完成阶段：V11 Grounded Answer / Model Provider Boundary（已实现、review、提交并归档）
```

RepoPilot 当前定位为面向代码仓库分析任务的可控 Code Agent Harness，不是替代通用 AI IDE 的编程助手。V1-V11 已完成实现；V11 已把 V10 Evidence Pack / Context Budget 接入 grounded answer 和 Model Provider Boundary，默认 fake provider 保持离线可验证，OpenAI-compatible provider 通过环境变量显式启用。

新增设计判断：RepoPilot adopts a grep-first, RAG-assisted retrieval stance。deterministic lexical/path/symbol search、exact match、文件树和路径线索是代码仓库分析的主要可审计检索基线；embedding/hybrid retrieval 只作为语义召回辅助。V11 Grounded Answer 应优先消费可审计证据，V12 Query Rewrite / Rerank 应服务于 grep-first baseline，不默认引入 Milvus、Elasticsearch、PgVector、Qdrant 或重型 embedding cache。

V8 已归档到：

```text
openspec/changes/archive/2026-05-20-v8-query-understanding-repo-rag/
```

V9 已归档到：

```text
openspec/changes/archive/2026-05-22-v9-embedding-hybrid-search/
```

V11 已归档到：

```text
openspec/changes/archive/2026-05-26-v11-grounded-answer-model-provider-boundary/
```

## 当前主链路

```text
API -> ChatService(trace_id) -> CodeAgent -> AgentLoop
  -> QueryUnderstanding/SearchPlan
  -> ToolRegistry -> PermissionPolicy -> ApprovalGate
  -> ToolExecutor(repo_rag) -> HybridRepoRetriever -> EvidencePack/ContextBudget
     -> GroundedAnswerGenerator -> ModelProvider
     -> LexicalRepoRetriever + EmbeddingRepoRetriever -> file_tools
```

`/chat` 顶层响应保持现有 contract：`trace_id`、`answer`、`related_files`、`tool_calls`。V7 的权限和审批审计、V8/V9 的 query understanding/retrieval 摘要、V10 的 Evidence Pack audit summary、V11 的 provider audit summary 只保留在内部 `trace_events_internal`，不作为 `/chat` 顶层字段暴露。

## V11 实现摘要

- 新增 `app/providers/model_provider.py`，提供 `ModelProvider` 边界、deterministic `FakeModelProvider`、`OpenAICompatibleModelProvider` 和环境变量 provider factory。
- 新增 `app/answering/grounded_answer.py`，提供 grounded answer、citation validation、fallback 和 provider audit 汇总。
- `AgentLoop` 在 successful `repo_rag` 且存在 Evidence Pack 后调用 `GroundedAnswerGenerator`；工具错误仍沿用原有失败回答。
- citation 格式为 `relative/path.py:start-end`；无合法 citation、越界 citation、provider error、timeout 或 invalid response 均降级为保守 fallback。
- 默认 provider 为 fake，默认验证不需要网络、API key 或真实模型输出。
- OpenAI-compatible provider 使用运行时依赖 `httpx`，通过 `REPOPILOT_MODEL_PROVIDER=openai_compatible`、`REPOPILOT_MODEL_BASE_URL`、`REPOPILOT_MODEL_API_KEY`、`REPOPILOT_MODEL_NAME` 显式启用。
- provider audit 不进入 `/chat` 顶层字段或 `tool_calls`，且不记录完整 prompt、完整模型输出、完整 Evidence Pack 或 API key。
- V11 仍不实现 query rewrite、rerank、memory、context compression、SandboxRunner、skill execution 或多 agent orchestration。
- 当前验证：
  - `openspec validate v11-grounded-answer-model-provider-boundary`：通过。
  - `pytest tests\test_model_provider.py tests\test_grounded_answer.py tests\test_agent_harness_kernel.py tests\test_chat_api.py`：54 passed。
  - `openspec validate --all`：8 passed, 0 failed。
  - `powershell -ExecutionPolicy Bypass -File scripts\verify.ps1`：通过；`pytest` 97 passed, 1 skipped；`ruff check .` All checks passed。
  - `git diff --check`：通过，仅有 CRLF 换行提示。
- Archive：`openspec archive v11-grounded-answer-model-provider-boundary --skip-specs -y` 已完成；长期 specs 已在 archive 前同步。
- Archive 后验证：`openspec validate --all`：7 passed, 0 failed；`powershell -ExecutionPolicy Bypass -File scripts\verify.ps1`：通过；`pytest` 97 passed, 1 skipped；`ruff check .` All checks passed；`git diff --check`：通过，仅有 CRLF 换行提示。
- 外部 review follow-up：
  - 已确认 `httpx>=0.27.0` 位于 `[project].dependencies`，并在 PROGRESS 中补充运行时依赖变更记录。
  - 已修正 citation 校验 allowed 集合，使其只接受实际传给 provider 的 included 且非空 snippet evidence。
  - `pytest tests\test_grounded_answer.py`：9 passed。

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
- 已将 `/chat` 的 repo_search 分支从简单 `search_code` 搜索升级为 V8 的 `ToolExecutor(repo_rag) -> LexicalRepoRetriever`；后续 V9 已进一步升级为 `HybridRepoRetriever`，当前 V10 在此基础上加入 Evidence Pack / Context Budget。
- 已同步长期 specs：
  - `openspec/specs/agent-loop-tool-execution/spec.md`
  - `openspec/specs/repo-query-understanding-rag/spec.md`

V8 不实现 embedding、Milvus、Elasticsearch、PgVector、Qdrant、LLM rewrite、rerank、memory、SandboxRunner、skill execution 或多 agent orchestration。

### V9：Embedding Retrieval + Hybrid Search

- 已提交：
  - `61a7963 Add V9 embedding hybrid search`
  - `24d4d6e Fix V9 review follow-ups`
  - `d31e83e Document V9 implementation review recovery`
  - `9479a0c Address final V9 review findings`
  - `e5e5fa0 Archive V9 embedding hybrid search`
- 已归档到：`openspec/changes/archive/2026-05-22-v9-embedding-hybrid-search/`
- 已实现 `DeterministicEmbeddingProvider`、`EmbeddingRepoRetriever`、`HybridRepoRetriever` 和 deterministic `hybrid_fuse`。
- 默认 embedding provider 是本地确定性实现，不调用网络、密钥、模型下载或外部服务。
- `ToolExecutor(repo_rag)` 和 `AgentLoop` 默认使用 `retrieval_mode=hybrid`，同时保留 lexical retrieval 作为一等通道。
- 内部 trace 记录 hybrid channel audit summary，包括 lexical、embedding、fused 结果数和 `min_fused_score`；该摘要不作为 `/chat` 顶层字段暴露。
- V9 不默认引入 Milvus、Elasticsearch、PgVector、Qdrant、真实外部 embedding 服务、模型下载、LLM rewrite、rerank、memory 或 context compression。

## 当前 Harness 状态

- `.harness/allowed_files.md` 已同步为 V10 implementation 边界。
- `.harness/review_checklist.md` 已同步为 V10 implementation review 和 verification 清单，并保留 plan/review 停止点记录。
- `openspec/changes/v10-evidence-pack-context-budget/` 已创建 proposal、design、tasks 和 `specs/repo-query-understanding-rag/spec.md`。
- `openspec/changes/v9-embedding-hybrid-search/` 已归档到 `openspec/changes/archive/2026-05-22-v9-embedding-hybrid-search/`。
- `openspec/changes/v10-evidence-pack-context-budget/` 已归档到 `openspec/changes/archive/2026-05-26-v10-evidence-pack-context-budget/`。
- `openspec/specs/repo-query-understanding-rag/spec.md` 已同步 V10 长期规格，包括 Evidence Pack、Context Budget 和 `min_fused_score=0.35` 口径。
- 当前已实现 V10 运行时代码，内部 self-review 和外部 review 均无阻塞发现，已提交并归档。
- V9 验证结果：
  - `openspec validate --all`：6 passed, 0 failed
  - `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`：通过；`pytest` 67 passed, 1 skipped；`ruff check .` All checks passed
  - `git diff --check`：通过，仅有 CRLF 换行提示
- V9 文档漂移修正：
  - 已补齐 README 的 V9 阶段历史；当前路线图已更新为“已完成至 V10，后续从 V11 开始”。
  - 已修正 ARCHITECTURE 当前架构段落中仍指向 V8 lexical RAG 的过期措辞。
  - 已补充本 handoff 的 V9 完整摘要。
  - 当前未提交工作区验证：`openspec validate --all` 7 passed, 0 failed；`powershell -ExecutionPolicy Bypass -File scripts\verify.ps1` 通过，`pytest` 67 passed, 1 skipped，`ruff check .` All checks passed；`git diff --check` 通过，仅有 CRLF 提示。

## V10 实现摘要

- 新增 `app/rag/evidence.py`，提供内部 Evidence Pack、Evidence item 和 Context Budget。
- `ToolExecutor.search_repo_rag` 在 successful hybrid retrieval 后生成 `ToolExecutionResult.evidence_pack`；工具错误时不伪造 Evidence Pack。
- Evidence item 固定包含 `evidence_id`、`file_path`、`start_line`、`end_line`、`score`、`snippet`、`source_summary`、`included` 和 `truncated`。
- Context Budget 默认 `max_context_chars=4000`，按 retrieval 顺序纳入 evidence，必要时裁剪最后一条。
- 内部 audit summary 固定包含 `evidence_items`、`included_count`、`omitted_count`、`truncated_count`、`budget_used_chars` 和 `max_context_chars`。
- `evidence_pack` 不进入 `call_summary()`、`/chat.tool_calls` 或 `/chat` 顶层响应。
- V10 仍不实现 grounded answer、model provider、prompt assembly、query rewrite、rerank、memory 或 context compression。
- V10 最新验证：
  - `openspec validate v10-evidence-pack-context-budget`：通过。
  - `pytest tests\test_evidence_pack.py tests\test_agent_harness_kernel.py tests\test_chat_api.py`：40 passed。
  - `powershell -ExecutionPolicy Bypass -File scripts\verify.ps1`：通过；`pytest` 75 passed, 1 skipped；`ruff check .` All checks passed。
  - `git diff --check`：通过，仅有 CRLF 换行提示。
- V10 review 收口：
  - 内部 self-review 未发现 P0/P1 阻塞；发现的 P2 历史文档措辞债已修正。
  - 外部 review：用户反馈外部 review 显示没问题，无阻塞发现。
  - 外部 review 后 full verify：`powershell -ExecutionPolicy Bypass -File scripts\verify.ps1` 通过；`pytest` 81 passed, 1 skipped；`ruff check .` All checks passed。
  - 实现提交：`c5ec1ff Add V10 evidence pack context budget`。
  - Archive：已移动到 `openspec/changes/archive/2026-05-26-v10-evidence-pack-context-budget/`，并同步长期 `repo-query-understanding-rag` spec。
  - Archive 后验证：`openspec validate --all` 6 passed, 0 failed；`powershell -ExecutionPolicy Bypass -File scripts\verify.ps1` 通过，`pytest` 81 passed, 1 skipped，`ruff check .` All checks passed；`git diff --check` 通过，仅有 CRLF 提示。
- V10 review follow-up：
  - 已修正长期 `agent-loop-tool-execution` spec，允许 repo-local deterministic hybrid RAG，不再禁止 V9 的本地 deterministic embedding retrieval。
  - 已把 `docs/FEATURE_LIST.json` 的 V8 条目标注为历史 lexical 验收口径，并指向当前 V9/V10 hybrid 口径。
  - `openspec validate --all`：7 passed, 0 failed。
  - `powershell -ExecutionPolicy Bypass -File scripts\verify.ps1`：通过；`pytest` 76 passed, 1 skipped；`ruff check .` All checks passed。
- V10 计划债务扫描修复：
  - 已修正 handoff 和 architecture 中残留的“当前 V9”口径。
  - 已把 V10 design 的实施前 `Migration Plan` 改成已执行的 implementation notes。
  - 已修正 Evidence Pack `original_query`，现在使用 `SearchPlan.original_query` 而不是提取后的 keyword。
  - 已修正 answer citation 过滤，混合相对路径和绝对路径结果时不把绝对路径写进 `/chat` answer。
  - `pytest tests\test_agent_harness_kernel.py tests\test_chat_api.py tests\test_evidence_pack.py`：42 passed。
  - `powershell -ExecutionPolicy Bypass -File scripts\verify.ps1`：通过；`pytest` 77 passed, 1 skipped；`ruff check .` All checks passed。
- 非 V10 历史代码债修复：
  - 已修正 V9 `hybrid_fuse` 默认阈值，强 embedding-only 命中可进入 hybrid 结果；`min_fused_score` 当前为 `0.35`。
  - 已把 AgentLoop 权限检查对象从底层 `search_code` 改为实际执行工具 `repo_rag`，并同步长期 `agent-loop-tool-execution` spec。
  - 已给 capability status 独立 route，英文状态问法不再进入 repo retrieval。
  - 已让普通英文问候避免误触发 repo_search，并清理测试中的部分 V8 命名噪音。
  - `pytest tests\test_repo_rag.py tests\test_agent_harness_kernel.py tests\test_chat_api.py`：50 passed。
  - `powershell -ExecutionPolicy Bypass -File scripts\verify.ps1`：通过；`pytest` 81 passed, 1 skipped；`ruff check .` All checks passed。
  - `openspec validate --all`：7 passed, 0 failed；`git diff --check`：通过，仅有 CRLF 换行提示。
- 已知剩余代码债：
  - `app/rag/evidence.py` 空 snippet 审计语义还可更干净，后续可改成 omitted 或跳过。
  - `app/harness/kernel.py` capability-status 仍是字符串规则集合，后续能力项增多时可抽成 classifier。
  - `app/rag/repo_rag.py` hybrid fusion 权重和阈值仍是硬编码常量，后续可参数化。
  - tests 中仍有少量历史阶段命名，可在测试清理时统一改成阶段无关命名。
- V10 前文档债扫描：
  - 已修正 `openspec/specs/README.md` 仍停留在 OpenSpec 初始化阶段的旧口径。
  - 已修正 `openspec/changes/README.md` 关于 legacy specs 迁移的旧口径。
  - 已修正 `docs/PROGRESS.md` 当前状态中的“当前 V4/V5 状态”措辞。
  - 已修正本 handoff V8 摘要中的“当前 V9 分支”措辞。

## 下一轮建议

1. 将 V11 archive 后文档更新提交到当前 feature 分支。
2. 如要收口 V11 分支，按项目流程合并/推送到 `main`。
3. 开始 V12 前先创建 Query Rewrite + Rerank 的 OpenSpec proposal/design/tasks/spec delta，并同步 `.harness/allowed_files.md` 与 `.harness/review_checklist.md`。

后续路线已拆分：V10 做 Evidence Pack + Context Budget；V11 做 Grounded Answer / Model Provider Boundary；V12 做 Query Rewrite + Rerank；V13 做 Memory；V14 做 Long Task / ReAct / Subagents；V15 做 Personal Assistant Gateway。
旧 V8 archive 中保留的是当时路线记录，已被后续 V9/V10 路线重排 supersede；当前长期 docs/specs 以 README、PROGRESS、ARCHITECTURE 和长期 OpenSpec specs 为准。
