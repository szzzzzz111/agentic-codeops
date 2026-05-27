# RepoPilot

RepoPilot 是一个面向代码仓库分析任务的可控 Code Agent Harness。它不是通用 AI IDE 或 AI 编程助手的替代品，而是围绕 Agent 的工具调用、安全边界、执行追踪、评测和交接机制，构建一个可验证、可审计、可扩展的代码智能体执行框架。

当前应用场景包括代码仓库阅读、Bug 定位和修复建议。项目价值不在于“更会写代码”，而在于让 Agent 执行过程有明确边界、可观察输出和可交接规则。

## 当前快照

- 当前主线能力：V1-V11 已归档；V12 Query Rewrite + Rerank 已实现并提交，OpenSpec change 已 Complete，等待人工确认是否归档。
- 当前 `/chat` contract：响应保留 `trace_id`、`answer`、`related_files`、`tool_calls`，不新增必需顶层字段。
- 当前检索与回答方式：deterministic query understanding + bounded deterministic multi-query rewrite + repo-local hybrid RAG（lexical + 轻量 deterministic embedding）+ before-Evidence rerank，内部生成 Evidence Pack 与字符级 Context Budget，并通过 grounded answer 边界生成基于证据的 `answer`。
- 当前安全边界：只读文件工具、`ToolRegistry`、`PermissionPolicy`、`ApprovalGate` 和统一 `ToolExecutor`。
- 当前默认不接真实 LLM，不执行 shell，不自动修改代码，不执行 skill；显式配置后可通过 OpenAI-compatible Model Provider 生成 grounded answer。
- 当前不默认接入真实外部 embedding 服务、Milvus、Elasticsearch、PgVector、Qdrant、真实 LLM query rewrite/rerank、memory 或 context compression。

## 当前能力

### Chat API

- 提供 FastAPI 应用和 `POST /chat`。
- 请求字段包含 `user_id`、`session_id`、`message` 和 `repo_path`。
- 每次请求生成唯一 `trace_id`。
- `related_files` 和 `tool_calls` 返回真实只读检索结果摘要。

### Query Understanding + Hybrid Repo RAG

- `QueryUnderstanding` 生成 deterministic `SearchPlan`。
- `SearchPlan` 包含 `question_type`、`keywords`、`symbols`、`path_hints`、`max_results` 和 `retrieval_mode=hybrid`。
- `ToolExecutor.search_repo_rag(...)` 是 `repo_rag` 审计入口。
- `LexicalRepoRetriever` 负责 repo 文本 chunk、lexical scoring、dedup 和 citation。
- `DeterministicEmbeddingProvider` 与 `EmbeddingRepoRetriever` 提供本地确定性 embedding retrieval，不依赖网络、密钥、模型下载或外部服务。
- `HybridRepoRetriever` 通过 deterministic fusion 合并 lexical 与 embedding 结果，并保留路径、文件名、符号和 exact token 命中的优势。
- citation 使用相对 repo 路径和 1-based 行号；`related_files` 来自 citation 文件路径。
- `EvidencePack` 将 retrieval results 整理为内部 evidence items，每条 item 包含稳定 `evidence_id`、相对 `file_path`、1-based 行号、`score`、`snippet`、`source_summary`、`included` 和 `truncated`。
- Context Budget 默认 `max_context_chars=4000`，按 retrieval 既有排序纳入 evidence，必要时裁剪最后一条，并只把摘要写入内部 trace/audit。

### Grounded Answer + Model Provider

- `GroundedAnswerGenerator` 只消费预算内 included evidence snippets 和 citation metadata。
- 默认 `FakeModelProvider` 是本地 deterministic provider，默认验证不依赖网络、密钥或真实模型输出。
- 可选 `OpenAICompatibleModelProvider` 通过环境变量启用：`REPOPILOT_MODEL_PROVIDER=openai_compatible`、`REPOPILOT_MODEL_BASE_URL`、`REPOPILOT_MODEL_API_KEY`、`REPOPILOT_MODEL_NAME`。
- provider 输出必须包含合法 citation，格式为 `relative/path.py:start-end`；无证据、无合法 citation、越界 citation 或 provider 失败时返回保守 fallback。
- provider audit 只保留在内部 trace，且不记录完整 prompt、完整模型输出、完整 Evidence Pack 或 API key。

### Safe Repository Tools

底层文件工具只读，不执行 shell 命令：

- `list_files(repo_path)`
- `read_file(repo_path, file_path, max_chars=12000)`
- `search_code(repo_path, keyword, max_results=20)`

文件工具会把访问限制在 `repo_path` 内，拒绝路径穿越，跳过忽略目录，过滤 `.env` 和私钥等敏感文件，忽略二进制文件，并限制读取和搜索返回规模。

### Permission And Trace

- `RequestRouter` 将请求路由到 `repo_search` 或 `chat_only`。
- `ToolRegistry` 记录只读低风险工具元数据。
- `PermissionPolicy` 和 `ApprovalGate` 在工具调用前做 `allow`、`deny` 或 `ask` 决策。
- `TraceEvent` 在 Kernel 内部记录路由、query understanding、权限、审批、工具调用、工具结果和拒绝事件。
- 内部 trace 当前不作为 `/chat` 顶层字段返回。

### Skill Loaders

当前只提供 skill 发现和按需读取，不执行 skill，也不把 skill loader 接入 `/chat` 决策。

- `load_skill_metadata(repo_path)`：发现 `.agents/skills/*/SKILL.md`，只解析 `name`、`description` 和相对仓库 `path`。
- `load_skill_content(repo_path, skill_path)`：按相对路径读取 `.agents/skills/<skill>/SKILL.md`，返回 `path` 和完整 `content`。

## 快速开始

启动服务：

```bash
uvicorn app.main:app --reload
```

接口地址：

```text
http://127.0.0.1:8000
```

运行测试：

```bash
pytest
```

可选静态检查：

```bash
ruff check .
```

默认验证入口：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/verify.ps1
```

## 请求示例

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "u001",
    "session_id": "s001",
    "message": "帮我分析 UNIQUE_BUG_TOKEN",
    "repo_path": "./mock_repo"
  }'
```

响应示例：

```json
{
  "trace_id": "trace_xxx",
  "answer": "基于仓库证据，问题 `帮我分析 UNIQUE_BUG_TOKEN` 的相关实现位于 app/example.py:1-3。",
  "related_files": ["app/example.py"],
  "tool_calls": [
    {
      "tool_name": "repo_rag",
      "keyword": "UNIQUE_BUG_TOKEN",
      "question_type": "code_location",
      "retrieval_mode": "hybrid",
      "status": "success",
      "result_count": "1"
    }
  ]
}
```

## 当前架构

```text
API -> ChatService(trace_id) -> CodeAgent -> AgentLoop
  -> QueryUnderstanding/SearchPlan -> QueryRewriteProvider
  -> ToolRegistry -> PermissionPolicy -> ApprovalGate
  -> ToolExecutor(repo_rag) -> HybridRepoRetriever -> Reranker -> EvidencePack/ContextBudget
     -> GroundedAnswerGenerator -> ModelProvider
     -> LexicalRepoRetriever + EmbeddingRepoRetriever -> file_tools
```

主要模块：

- `app/main.py`：创建 FastAPI 应用并注册路由。
- `app/api/chat.py`：暴露聊天接口。
- `app/schemas/chat.py`：定义请求和响应模型。
- `app/services/chat_service.py`：创建请求级 `trace_id` 并编排智能体调用。
- `app/agents/code_agent.py`：调用轻量 `AgentLoop` 并适配 `/chat` 响应结构。
- `app/harness/kernel.py`：提供 RequestRouter、QueryUnderstanding 接入、ToolRegistry、PermissionPolicy、ApprovalGate、AgentLoop 和 TraceEvent 最小 Kernel。
- `app/rag/query_understanding.py`：提供 deterministic `SearchPlan`。
- `app/rag/repo_rag.py`：提供 repo chunk、lexical scoring、deterministic embedding、hybrid fusion、dedup 和 citation。
- `app/rag/query_rewrite.py`：提供 deterministic multi-query rewrite 边界和 Code Evidence variants。
- `app/rag/rerank.py`：提供 before-Evidence deterministic rerank 边界。
- `app/rag/evidence.py`：提供内部 Evidence Pack 和 deterministic character Context Budget 结构。
- `app/answering/grounded_answer.py`：提供 grounded answer、citation 校验、fallback 和 provider audit 整理。
- `app/providers/model_provider.py`：提供 Model Provider 边界、fake provider、OpenAI-compatible provider 和环境变量配置。
- `app/tools/tool_executor.py`：统一包装只读代码搜索、hybrid repo RAG 和 skill loader 工具调用。
- `app/tools/file_tools.py`：提供安全仓库文件工具。
- `app/tools/skill_loader.py`：提供 Skill Metadata Loader 和 Skill Content Loader。
- `app/observability/tracing.py`：生成请求级 `trace_id`；当前不是完整持久化审计系统。

## 阶段历史

### V1：Agent 服务入口和可追踪请求结构

建立 `POST /chat`、`ChatRequest` / `ChatResponse`、`trace_id`、`related_files`、`tool_calls` 和接口测试。

### V2：安全只读仓库工具层

建立 `list_files`、`read_file`、`search_code`，并加入 repo 路径边界、路径逃逸防护、敏感文件过滤、忽略目录和二进制文件过滤。

### V3：统一工具执行边界

把工具调用收口到 `ToolExecutor`；`CodeAgent` 通过 `ToolExecutor` 调用只读 `search_code`，并返回真实 `related_files` 和 `tool_calls` 摘要。

### V4：Skill Metadata Loader

发现 `.agents/skills/*/SKILL.md`，读取 YAML frontmatter 中的 `name` 和 `description`，只返回相对仓库路径，不读取完整 skill 正文。

### V5：Skill Content Loader

在 metadata-first 之后提供 progressive disclosure 的按需读取层，允许读取 `.agents/skills/<skill>/SKILL.md` 完整内容，但不解析 frontmatter、不接入 `/chat` 决策、不执行 skill。

### V6：Agent Harness Kernel + Router Kernel

建立 `AgentLoopRequest`、`RouteDecision`、`ToolSpec`、`TraceEvent` 和轻量 `AgentLoop`，把现有搜索链路包进可演进的 Harness Kernel。

### V7：Permission + Approval Gate

加入 `ToolSpec.requires_approval`、`PermissionPolicy` 和最小 `ApprovalGate`，确定性产出 `allow`、`deny` 或 `ask`，并确保 `deny` / `ask` 分支不调用 executor。

### V8：Query Understanding + Lexical Repo RAG

将旧路线里的“大 Repo RAG Engineering”收窄为可落地的非向量化 repo-local RAG 骨架：deterministic query understanding、repo chunk、lexical scoring、citation 和稳定 `/chat` contract。

### V9：Embedding Retrieval + Hybrid Search

在 V8 lexical repo RAG 之上加入轻量 embedding retrieval，并保持只读、安全、repo-local 和 `/chat` contract 边界。V9 提供 `DeterministicEmbeddingProvider`、`EmbeddingRepoRetriever`、`HybridRepoRetriever` 和 deterministic `hybrid_fuse`，默认使用本地固定维度向量，不调用网络、密钥、模型下载或外部服务。

V9 保留 lexical retrieval 作为一等通道，通过 hybrid fusion 合并 lexical 与 embedding 结果，并让路径、文件名、符号和 exact token 命中的优势不被 embedding 相似度淹没。内部 trace 可记录 lexical、embedding、fused 结果数和 `min_fused_score`；这些审计摘要不作为 `/chat` 顶层字段暴露。

### V10：Evidence Pack + Context Budget

在 V9 hybrid repo RAG 之后加入内部 Evidence Pack 和 deterministic character Context Budget。`ToolExecutionResult.evidence_pack` 只作为内部字段持有，不进入 `call_summary()`、`/chat.tool_calls` 或 `/chat` 顶层响应。

V10 的 trace/audit 只记录 Evidence Pack 摘要：`evidence_items`、`included_count`、`omitted_count`、`truncated_count`、`budget_used_chars` 和 `max_context_chars`。V10 不实现 grounded answer、model provider、prompt assembly、query rewrite、rerank、memory 或 context compression。

### V11：Grounded Answer / Model Provider Boundary

在 V10 Evidence Pack / Context Budget 之后加入 grounded answer 和 Model Provider Boundary。默认使用本地 deterministic fake provider；显式配置后可使用 OpenAI-compatible provider。模型只消费预算内 included evidence，不参与检索规划、工具调用、query rewrite、rerank、memory 或多步 agent 决策。

V11 保持 `/chat` 顶层响应 contract 不变，grounded answer 写入现有 `answer` 字段。Provider audit 只保留在内部 trace，不进入 `/chat.tool_calls` 或顶层响应。

### V12：Query Rewrite + Rerank

在 V11 grounded answer 边界之前的检索链路加入 bounded deterministic multi-query rewrite 和 before-Evidence rerank。默认 rewrite provider 永远保留 `original` variant，并按 `definition -> usage -> configuration -> tests` 生成最多 3 条 Code Evidence variants；rerank 只在 retrieval results 层选择最多 `SearchPlan.max_results` 条结果进入 Evidence Pack。

V12 保持 Evidence Pack budget/summary 和 grounded answer citation validation 语义不变；rewrite/rerank audit 只保留在内部 trace，不进入 `/chat.tool_calls` 或顶层响应。V12 不默认启用真实 LLM rewrite/rerank。

## 当前非目标

- 默认接入真实 LLM；真实 provider 仅作为显式配置的 OpenAI-compatible provider。
- 技能执行。
- SandboxRunner 实现。
- trace 持久化审计。
- 反思检查和 eval。
- 真实外部 embedding 服务、Milvus、Elasticsearch、PgVector、Qdrant。
- 真实 LLM query rewrite/rerank 和 context compression。
- Memory。
- 自动修改代码。
- shell 执行。
- 复杂智能体循环、LLM 驱动语义理解和多步规划。
- 多 agent orchestration。

## 工程化取向

RepoPilot 后续路线要体现工程化味道，但不追求重型企业平台。由于当前主要由个人配合 AI 开发，工程化优先体现在边界、审计、验证、可替换接口和交接文档，而不是堆中间件或堆代码量。

- 清晰边界：Provider、Router、AgentLoop、ToolRegistry、ToolExecutor、Memory、RAG、Skill、Trace 分层明确。
- 可审计：每次 model/tool/skill/memory 调用都有结构化摘要，敏感内容默认不外泄。
- 可验证：每个阶段都有最小测试和 `scripts/verify.ps1` 入口。
- 可替换：RAG、Memory、Model Provider、向量库和存储都先做接口，默认实现保持轻量。
- 可交接：OpenSpec、harness、PROGRESS 和 HANDOFF 必须同步，不把关键项目知识只留在聊天里。

暂不追求：

- 一开始就引入复杂微服务、Kafka、Milvus、Elasticsearch、PostgreSQL 等重依赖。
- 一次性做完整企业级权限、观测、队列、分布式任务系统。
- 为了“看起来工程化”而增加个人维护不起的代码量。

## Harness Engineering

本仓库包含一套轻量 Harness V0，用来让 Agent 开发过程可控、可验证、可交接：

- `AGENTS.md`：Agent 入口地图。
- `openspec/specs/`：长期能力规格入口。
- `docs/ARCHITECTURE.md`：架构边界。
- `docs/AGENT_RULES.md`：Agent 工作规则。
- `docs/PROGRESS.md`：项目长期进度记忆。
- `docs/FEATURE_LIST.json`：可验收功能清单。
- `HANDOFF_TO_NEXT_CHAT.md`：跨 session 交接文档。
- `scripts/verify.ps1`：本地验证入口。

OpenSpec、harness、review checklist 和 handoff 是开发流程约束，不是 RepoPilot runtime 功能。

## 后续安全架构

未来高风险能力应沿用当前 Kernel 链路，在进入实际 executor 前经过权限和审批边界：

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

权限检查、人工介入审批、工具调用审计和沙箱命令执行都应该围绕 `AgentLoop` / `ToolExecutor` 边界实现，不应该散落在 `main.py`、API handler 或具体工具函数里。

## 路线图

已归档至 V11：Grounded Answer / Model Provider Boundary；V12 Query Rewrite + Rerank 已实现并提交，等待人工确认是否归档。后续路线：

- V13：Memory，区分 STM、LTM 和 PREF，并加入 memory audit。
- V14：Long Task / ReAct / Subagents，支持计划、任务状态、pause/resume、scratch space、subagents 和 worktree handoff。
- V15：Personal Assistant Gateway，探索 always-on、heartbeat/cron、connector、通知和人工审批。
