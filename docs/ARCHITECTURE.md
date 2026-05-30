# 架构说明

RepoPilot 当前采用渐进式 Harness 架构。目标不是替代通用 AI IDE 或 AI 编程助手，而是围绕代码仓库分析任务，把 Agent 的工具调用、安全边界、执行追踪、验证和交接机制做成可控、可审计、可扩展的执行框架。

## 当前主链路

```text
API -> ChatService(trace_id) -> CodeAgent -> AgentLoop
  -> MemoryManager(STM/PREF/LTM command/read audit)
  -> LongTaskManager(command/status/step audit)
  -> QueryUnderstanding/SearchPlan -> QueryRewriteProvider
  -> ToolRegistry -> PermissionPolicy -> ApprovalGate
  -> ToolExecutor(repo_rag) -> HybridRepoRetriever -> Reranker -> EvidencePack/ContextBudget
     -> GroundedAnswerGenerator -> ModelProvider
     -> LexicalRepoRetriever + EmbeddingRepoRetriever -> file_tools
```

- API 层只接收请求并返回响应。
- `ChatService` 负责编排请求、生成 `trace_id`、调用智能体。
- `CodeAgent` 负责调用轻量 `AgentLoop` 并适配 `/chat` 响应结构。
- `MemoryManager` 负责明确 memory 指令、repo-local SQLite PREF/LTM、进程内 STM 和脱敏 memory audit。Memory command 在 `RequestRouter` / keyword 路由前识别。
- `LongTaskManager` 负责明确长任务指令、repo-local SQLite task store、deterministic task-type plan、pause/resume、scratch 摘要和 ReAct trace skeleton。Long Task 控制命令在 memory command 之后、`RequestRouter` / keyword 路由前处理；只有显式 resume/run 当前 step 才能调用只读 `repo_rag`。
- `QueryUnderstanding` 负责 deterministic 检索前理解，产出 `SearchPlan`。
- `QueryRewriteProvider` 负责 bounded deterministic multi-query rewrite，默认生成 `original` 和最多 3 条 Code Evidence variants。
- `ToolExecutor` 统一收口工具执行，当前包装只读 `search_code` 和 `repo_rag`。
- `LexicalRepoRetriever` 负责 repo-local chunk、lexical scoring、dedup 和 citation。
- `EmbeddingRepoRetriever` 使用本地确定性 embedding provider 对 repo chunk 做轻量 embedding retrieval。
- `HybridRepoRetriever` 负责合并 lexical 与 embedding retrieval 结果。
- `Reranker` 负责在 Evidence Pack 前对 merged retrieval results 做 deterministic rerank，并最多选择 `SearchPlan.max_results` 条结果。
- `EvidencePack` / `ContextBudget` 在 retrieval 后生成内部证据输入层和字符级预算摘要。
- `GroundedAnswerGenerator` 只消费预算内 included evidence，并负责 provider 调用、citation 校验、fallback 和脱敏 audit 摘要。
- `ModelProvider` 默认使用本地 deterministic fake provider；显式配置后可调用 OpenAI-compatible provider。
- `file_tools` 提供安全仓库文件工具，不处理 HTTP 或 Agent 决策。
- Trace 贯穿请求生命周期，由 `ChatService` 创建请求级唯一 `trace_id`，并随 `/chat` 响应返回。当前 Trace 仍是请求级标识，不是完整持久化审计系统；hybrid retrieval 的 channel audit summary、Evidence Pack audit summary 和 provider audit summary 只保留在内部 trace，不作为 `/chat` 顶层字段暴露。

当前 `/chat` 已通过 hybrid repo RAG 与 grounded answer 边界返回带 citation 的证据约束回答，并支持 repo-local SQLite-backed Memory 指令。V14 active change 正在加入 Long Task Control Plane：任务状态写入 `.repopilot/tasks.sqlite3`，控制命令不调用 repo_rag，显式 resume/run 每次只推进一个只读 repo_rag step。默认不接真实 LLM、不自动修改代码、不执行 shell；显式配置后可通过 OpenAI-compatible provider 生成 grounded answer，并可作为 Long Task plan 字段增强来源。

## 检索设计原则：grep-first, RAG-assisted

RepoPilot adopts a grep-first, RAG-assisted retrieval stance: deterministic lexical/path/symbol search remains the primary auditable baseline, while embedding/hybrid retrieval is an auxiliary channel for semantic recall.

对代码仓库分析任务，函数名、类名、错误名、配置 key、路径、测试名和调用点等 exact match 往往比泛语义 embedding 更可靠、更便宜、更可审计。因此当前和后续检索链路应遵守：

- deterministic code search、lexical search、path search 和 symbol search 是主通道。
- embedding retrieval、hybrid retrieval、query rewrite 和 rerank 只能辅助召回或排序，不替代 grep-like baseline。
- 对包含 `symbols` 或 `path_hints` 的高精度查询，hybrid retrieval 使用 lexical anchor，embedding-only result 不能单独绕过 lexical/path/symbol 命中进入证据池。
- Evidence Pack 和 Grounded Answer 应优先消费可审计的 lexical/path/symbol evidence，并通过 citation 约束回答。
- V12 Query Rewrite / Rerank 必须服务于 grep-first 检索基线，不能把系统改成默认向量库优先。
- V13 Memory 只能作为偏好和用户明确项目事实的本地状态层，不能替代 repo evidence 或 citation validation。
- V14 Long Task 的 step action 仍只能通过 grep-first, RAG-assisted 的 `repo_rag` 执行；scratch 和 ReAct trace 不能替代 repo evidence 或 citation validation。
- 不默认引入 Milvus、Elasticsearch、PgVector、Qdrant 或重型 embedding cache；只有后续 repo 规模和任务类型明确需要时再通过单独阶段评估。

## V2 工具层：安全只读仓库能力

V2 新增安全只读文件工具：

```text
app/tools/file_tools.py
```

包含：

- `list_files(repo_path)`
- `read_file(repo_path, file_path, max_chars=12000)`
- `search_code(repo_path, keyword, max_results=20)`

这些工具限制访问在 `repo_path` 内，拒绝路径逃逸，跳过敏感文件、隐藏目录、忽略目录和二进制文件。V3 当前已经通过 `ToolExecutor` 把 `search_code` 接入 `/chat`。

## V3 执行层：ToolExecutor

V3 新增：

```text
app/tools/tool_executor.py
```

V3 职责：

- 调用 `search_code`。
- 捕获工具错误并返回结构化摘要。
- 生成 `tool_calls` 所需的工具名称、关键词、状态和结果数量。
- 不返回完整文件内容、完整搜索结果或本机绝对路径。

`ToolExecutor` 当前不是通用插件平台，不动态注册任意工具，不实现权限系统、人工审批或沙箱执行。

## 后续工具执行边界

未来高风险工具调用应继续沿用当前 Kernel 链路，在进入实际 executor 前经过权限和审批边界：

```text
ChatService
  -> CodeAgent
  -> AgentLoop
  -> ToolRegistry
  -> PermissionPolicy
  -> ApprovalGate
  -> ToolExecutor
  -> SandboxRunner（仅未来命令类工具）
  -> 具体工具
```

这样权限管理、人工审批、工具调用审计和沙箱执行都可以增量加入，不需要推倒当前 API、Service、Agent 分层。V7 当前只实现确定性 `PermissionPolicy` 和最小 `ApprovalGate`，真实审批流程和 `SandboxRunner` 仍留到后续阶段。

`PermissionPolicy` 和最小 `ApprovalGate` 已在 V7 中作为确定性运行时边界实现；`ApprovalGate` 当前不做真实交互审批或持久化。`SandboxRunner` 仍是 Roadmap，不是当前已实现能力。

## 架构约束

- `main.py` 只创建应用和注册 router。
- API 层不直接读文件、不执行工具、不写业务逻辑。
- Service 层负责编排，不直接实现仓库搜索细节。
- Agent 层负责决策和组织工具调用。
- Tools 层只提供可调用能力，不处理 HTTP。
- `ToolExecutor` 负责统一执行入口和工具调用摘要，不承载复杂业务推理。
- `PermissionPolicy` 负责在工具调用前产出 `allow`、`deny` 或 `ask` 决策。
- `ApprovalGate` 当前只消费权限决策并阻止 `ask` 分支执行工具，不实现真实审批 UI。
- 高风险能力以后必须经过 `ToolExecutor`，不能散落在各模块里。

## 暂不引入

- 默认接入真实 LLM；真实 provider 仅作为显式配置的 OpenAI-compatible provider。
- LangGraph。
- 真实外部 embedding 服务、向量库、真实 LLM query rewrite/rerank、向量 memory、自动 memory 总结或 context compression。
- 多 Agent。
- 后台任务、自动循环执行、真实 subagent orchestration 或 worktree automation。
- 自动修改代码。
- 沙箱执行命令。
- SandboxRunner 的实际实现。
- 真实审批 UI 或审批持久化。
- trace 持久化审计。

## V8 历史架构补充：Query Understanding + Lexical Repo RAG

V8 在 V7 权限/审批边界之后接入非向量化 repo-local RAG。该阶段已归档；以下链路描述 V8 历史实现，不是当前主链路：

```text
API -> ChatService(trace_id) -> CodeAgent -> AgentLoop
  -> QueryUnderstanding/SearchPlan
  -> ToolRegistry -> PermissionPolicy -> ApprovalGate
  -> ToolExecutor(repo_rag) -> LexicalRepoRetriever -> file_tools
```

边界约束：

- `QueryUnderstanding` 是 deterministic 实现，不调用 LLM、embedding provider、向量库或外部服务。
- `SearchPlan` 只描述检索计划，不做权限决策。
- `ToolExecutor.search_repo_rag` 是 V8 的 `repo_rag` 审计入口，不属于 V3 原始 `search_code` 能力。
- `LexicalRepoRetriever` 通过安全文件工具读取允许访问的 repo 文本文件，并输出 citation。
- citation 只包含相对 repo 路径和 1-based 行号，不包含本机绝对路径。
- `/chat` 不新增顶层字段；内部 trace 可记录 query understanding 和 retrieval 摘要。

V8 仍不引入 embedding、Milvus、Elasticsearch、PgVector、Qdrant、LLM rewrite、rerank、memory、SandboxRunner 或多 agent orchestration。当前主链路已在 V9 hybrid retrieval 之后加入 V10 Evidence Pack / Context Budget，见后续章节。

## 后续路线调整

V9 已完成 Embedding Retrieval + Hybrid Search：补 embedding provider 边界、轻量默认实现、repo-local embedding retrieval 和 hybrid fusion，同时保留 V8 lexical retrieval 作为一等通道。当前路线进一步明确为 grep-first, RAG-assisted：lexical/path/symbol evidence 是可审计强基线，embedding/hybrid 只作为辅助召回通道。V9 不默认引入 Milvus、Elasticsearch、PgVector、Qdrant、真实外部 embedding 服务或模型下载。

V10 已完成 Evidence Pack + Context Budget；V11 已完成 Grounded Answer / Model Provider Boundary；V12 已完成 Query Rewrite + Rerank；V13 已完成 Memory；V14 做 Long Task / ReAct / Subagents；V15 做 Personal Assistant Gateway。

## V9 架构补充：Embedding Retrieval + Hybrid Search

V9 在 V8 lexical RAG 之上加入轻量 embedding retrieval，并保持只读、安全、repo-local 和 `/chat` contract 边界。当前执行链路为：

```text
API -> ChatService(trace_id) -> CodeAgent -> AgentLoop
  -> QueryUnderstanding/SearchPlan
  -> ToolRegistry -> PermissionPolicy -> ApprovalGate
  -> ToolExecutor(repo_rag) -> HybridRepoRetriever
     -> LexicalRepoRetriever + EmbeddingRepoRetriever -> file_tools
```

边界约束：

- `DeterministicEmbeddingProvider` 是本地确定性实现，不调用网络、密钥、模型下载或外部服务。
- `EmbeddingRepoRetriever` 复用安全文件工具允许访问的 repo 文本 chunk，并输出相对路径 citation。
- `HybridRepoRetriever` 对 lexical 和 embedding 结果做 deterministic fusion，保留路径、文件名、符号和 exact token 命中的优势。
- 内部 trace 记录 hybrid channel audit summary，包括 lexical、embedding、anchored embedding、fused 结果数和 `min_fused_score`；该摘要不作为 `/chat` 顶层字段暴露。
- V9 不默认引入 Milvus、Elasticsearch、PgVector、Qdrant、真实外部 embedding 服务或持久化向量索引。
- V9 不实现 LLM query rewrite、LLM rerank、grounded answer、model provider、memory 或 context compression。

## V10 架构补充：Evidence Pack + Context Budget

V10 在 V9 hybrid retrieval 之后增加内部 Evidence Pack 输入层，用来给后续 grounded answer / model provider boundary 准备可审计证据结构。当前执行链路为：

```text
ToolExecutor(repo_rag)
  -> HybridRepoRetriever
  -> EvidencePack
  -> ContextBudget(max_context_chars=4000)
  -> AgentLoop internal trace summary
```

边界约束：

- `EvidencePack` 来自 retrieval results，不直接读取仓库文件、不调用 shell、不改变 retrieval 排序。
- 每条 evidence item 包含稳定 `evidence_id`、相对 `file_path`、1-based `start_line` / `end_line`、`score`、`snippet`、`source_summary`、`included` 和 `truncated`。
- Context Budget 使用 deterministic character budget，默认 `max_context_chars=4000`；超预算时允许裁剪最后一条 evidence。
- 内部 audit summary 固定包含 `evidence_items`、`included_count`、`omitted_count`、`truncated_count`、`budget_used_chars` 和 `max_context_chars`。
- `ToolExecutionResult.evidence_pack` 只在内部持有，不进入 `call_summary()`、`/chat.tool_calls` 或 `/chat` 顶层响应。
- V10 不实现 grounded answer、model provider、prompt assembly、query rewrite、rerank、memory 或 context compression。

## V11 架构补充：Grounded Answer + Model Provider Boundary

V11 在 V10 Evidence Pack / Context Budget 之后增加回答生成边界。当前执行链路为：

```text
AgentLoop
  -> ToolExecutor(repo_rag)
  -> EvidencePack / ContextBudget
  -> GroundedAnswerGenerator
  -> ModelProvider(fake by default, openai_compatible when configured)
  -> citation validation / fallback
```

边界约束：

- `GroundedAnswerGenerator` 只消费预算内 included evidence snippets 和 citation metadata，不直接读仓库、不执行工具、不修改代码。
- 默认 `FakeModelProvider` 是本地 deterministic provider；默认验证不需要网络、API key 或真实模型输出。
- `OpenAICompatibleModelProvider` 只在显式环境变量配置后启用，使用 `httpx` 调用 chat completions 兼容接口。
- provider 输出必须引用 provided evidence citation，格式为 `relative/path.py:start-end`；无 citation、越界 citation、provider error 或 timeout 均返回保守 fallback。
- provider audit 只记录 provider name、model、status、error class 或 fallback reason，不记录完整 prompt、完整模型输出、完整 Evidence Pack、API key 或本机绝对路径。
- `/chat` 顶层响应仍只要求 `trace_id`、`answer`、`related_files` 和 `tool_calls`；provider audit 不进入 `tool_calls`。
- V11 不实现 query rewrite、rerank、memory、context compression、SandboxRunner、skill execution 或多 agent orchestration。

## 后续设计备忘：轻量 LLM Gateway

外部 LLMGateway 资料中的“稳定性控制面”概念对 RepoPilot 有参考价值，但本项目不应直接复制重型工业网关。当前已实现的是 V11 Model Provider Boundary，不是完整 LLMGateway：它只收口 provider 调用、环境变量配置、基础 timeout、错误 fallback、citation validation 和脱敏 provider audit。

后续如果增强真实模型调用，RepoPilot 应优先吸收轻量子集：

- 模型调用统一入口：继续围绕 `ModelProvider` / `GroundedAnswerGenerator`，不要让 API handler、AgentLoop 或工具层直接散落 HTTP 调用。
- 配置和密钥边界：API key 只来自环境变量或后续受控配置源，audit/log 不记录 key、完整 prompt、完整输出或完整 Evidence Pack。
- 超时和兜底：保留明确 timeout、provider error fallback、citation invalid fallback，让真实模型失败不破坏 `/chat` contract。
- 最小重试：如后续需要，只对网络瞬断、429/5xx 等可恢复错误做小次数、可测试的 deterministic retry；默认验证仍不得依赖真实网络。
- 轻量路由：只在明确需求出现时支持按任务类型选择 provider/model，例如 grounded answer、rewrite、rerank 分开配置；不要提前做复杂策略引擎。
- 成本/用量摘要：可以先记录 provider、model、status、latency、token/cost 估算字段，但只进入内部 trace 或后续受控审计，不进入 `/chat.tool_calls`。

暂不追求完整工业 LLMGateway 能力：全局限流服务、熔断集群、复杂供应商竞价、多租户配额、持久化成本账单、分布式日志追踪或控制台。只有当 RepoPilot 真的开始依赖多个真实 provider、长任务或 always-on gateway 时，再作为独立阶段评估。

## V12 架构补充：Query Rewrite + Rerank

V12 在 V11 检索与回答链路中加入 deterministic rewrite/rerank 边界。当前执行链路为：

```text
ToolExecutor(repo_rag)
  -> QueryRewriteProvider(deterministic)
  -> HybridRepoRetriever per query variant
  -> merged retrieval results
  -> Reranker(deterministic)
  -> EvidencePack / ContextBudget
```

边界约束：

- rewrite 永远保留 `original` variant，并最多生成 3 条 Code Evidence variants：`definition`、`usage`、`configuration`、`tests`。
- rewrite 不改变 route、权限决策或整体 `question_type`。
- rewrite variants 都会执行 hybrid retrieval；对 symbol/path 查询，embedding-only 弱命中仍需 lexical anchor。
- rerank 只作用于 retrieval results 层，不新增独立语义过滤阈值。
- Evidence Pack budget/summary 和 grounded answer citation validation 语义不变。
- rewrite/rerank audit 只保留在内部 trace，不进入 `/chat` 顶层字段或 `tool_calls`。
- V12 不默认启用真实 LLM rewrite/rerank、memory、context compression、SandboxRunner、skill execution 或多 agent orchestration。

## V13 架构补充：Memory

V13 在 AgentLoop 中加入轻量 Memory 边界：

```text
AgentLoop
  -> MemoryManager
     -> SQLiteMemoryStore(PREF/LTM in .repopilot/memory.sqlite3)
     -> InMemorySessionMemoryStore(STM)
  -> QueryUnderstanding/SearchPlan -> repo_search...
```

边界约束：

- Memory command 在 `RequestRouter` / keyword 路由前确认优先，命中后不执行 `repo_rag`。
- `.repopilot/` 是 repo-local 本地状态目录，必须被 git 忽略；Memory 不修改被分析仓库代码文件。
- `repo_key` 使用 resolved path、POSIX 分隔符、Windows lower-case 和稳定 hash；audit 不暴露绝对路径或 DB 路径。
- PREF/LTM 使用 SQLite 持久化，STM 使用进程内存储。
- Memory audit 只保留在内部 trace，不进入 `/chat` 顶层字段或 `tool_calls`。
- Memory 不实现向量召回、自动模型总结、跨 repo 智能召回、context compression、SandboxRunner、skill execution 或多 agent orchestration。

## V14 架构补充：Long Task Control Plane + ReAct Skeleton

V14 在 AgentLoop 前段加入 Long Task 控制面：

```text
AgentLoop
  -> MemoryManager(command)
  -> LongTaskManager
     -> SQLiteLongTaskStore(tasks in .repopilot/tasks.sqlite3)
     -> LongTaskPlanner(deterministic templates + provider-assisted fallback)
  -> resume/run step
     -> ToolRegistry -> PermissionPolicy -> ApprovalGate
     -> ToolExecutor(repo_rag)
```

边界约束：

- Long Task 指令解析优先于 `RequestRouter` / keyword 路由，并在 Memory command 之后处理；创建、查看、列出、暂停、补充、归档和 reopen 不调用 `repo_rag`。
- `.repopilot/tasks.sqlite3` 是 repo-local 本地状态；repo_key 复用 V13 resolved path、POSIX 分隔符、Windows lower-case 和稳定 hash 规则。
- 创建任务只保存 plan，不自动执行；显式 resume/run 每次最多推进一个 step。
- step action 仅允许现有只读 `repo_rag`，且必须经过 `ToolRegistry`、`PermissionPolicy`、`ApprovalGate` 和 `ToolExecutor`。
- ReAct trace 只保存 `thought_summary`、`action`、`observation_summary` 和 `status` 摘要；scratch 只保存用户目标、补充信息、observation 摘要和 citation 引用。
- Long Task audit 不进入 `/chat` 顶层字段；`tool_calls` 只保留实际 `repo_rag` 摘要。
- V14 不新增 `/tasks` API，不执行后台任务、不自动循环执行、不创建 worktree、不调度真实 subagents、不执行 shell、不自动修改代码、不做 evaluator/reflection。
