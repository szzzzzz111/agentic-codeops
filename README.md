# RepoPilot

RepoPilot 是一个面向代码仓库分析任务的可控 Code Agent Harness。它不是通用 AI IDE 或 AI 编程助手的替代品，而是围绕 Agent 的工具调用、安全边界、执行追踪、评测和交接机制，构建一个可验证、可审计、可扩展的代码智能体执行框架。

当前应用场景包括代码仓库阅读、Bug 定位和修复建议。项目价值不在于“更会写代码”，而在于让 Agent 执行过程有明确边界、可观察输出和可交接规则。

## 当前快照

- 当前主线能力：V1-V18 已归档；当前基线为 `main` / `agentic-codeops/main`，HEAD 为 `3c7a8b3`；当前无 active OpenSpec change，V18 Patch + Verify Loop 已实现、review、提交、归档、fast-forward 合并并推送。
- 当前 `/chat` contract：响应保留 `trace_id`、`answer`、`related_files`、`tool_calls`，不新增必需顶层字段。
- 当前检索与回答方式：deterministic query understanding + bounded deterministic multi-query rewrite + repo-local hybrid RAG（lexical + 轻量 deterministic embedding）+ before-Evidence rerank，内部生成 Evidence Pack 与字符级 Context Budget，并通过 grounded answer 边界生成基于证据的 `answer`。
- 当前 Memory：repo-local SQLite-backed PREF/LTM、进程内 STM、明确 `记住` / `忘记` / `remember` / `forget` 指令和内部 memory audit；`.repopilot/` 是本地状态目录，不提交到 git。
- 当前 Long Task：repo-local `.repopilot/tasks.sqlite3`、明确长任务指令、任务状态、pause/resume、scratch 摘要、quota/archive 和摘要级 ReAct trace；不新增 `/tasks` API 或 `/chat` 必需顶层字段。
- 当前 Assistant Control Surface：通过现有 `/chat.answer` 返回只读助手状态，聚合当前能力、Memory 计数和 Long Task 摘要；不新增 API、不新增 `/chat` 顶层字段、不调用 `repo_rag`、不写 memory、不创建任务。
- 当前 Safe Patch Authoring：通过明确 patch 请求基于 repo evidence 生成 pending patch proposal；默认 fake patch provider 不生成真实 diff，显式配置真实 provider 后可返回结构化 unified diff；用户必须明确 `确认 patch <patch_id>` / `应用 patch <patch_id>` 才能通过受控 `patch_apply` 写入。
- 当前 Verification Runner：通过明确验证请求运行固定白名单标签 `pytest`、`ruff` 或 `verify`，其中 `verify` 映射到 `scripts/verify.ps1`；执行必须经过 `verification_run` 权限/审批边界和 `ToolExecutor`，公开响应只返回截断脱敏摘要。
- 当前 Patch + Verify Loop：通过明确组合确认请求串联 pending patch apply 与白名单验证；组合请求必须同时包含 patch id 和验证标签，解析失败整体拒绝且不 apply；apply 成功后才使用独立 verification context 运行验证。
- 当前安全边界：只读文件工具、`ToolRegistry`、`PermissionPolicy`、`ApprovalGate`、`ToolInvocationContext` 和统一 `ToolExecutor`。
- 当前默认不接真实 LLM，不执行任意 shell，不执行 skill；V16 仅允许用户明确确认后的受控 patch apply；V17 仅允许明确验证请求下的白名单验证命令；V18 仅允许明确组合确认下的 apply 后 verify；显式配置后可通过 OpenAI-compatible Model Provider 生成 grounded answer。
- 当前不默认接入真实外部 embedding 服务、Milvus、Elasticsearch、PgVector、Qdrant、真实 LLM query rewrite/rerank、向量 memory、自动 memory 总结或 context compression。
- 当前不执行后台任务、不创建 worktree、不调度真实 subagents、不执行 shell、不自动运行测试或 commit；V16 仅允许用户明确确认后的受控 patch apply。

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

### Memory

- `MemoryManager` 解析明确 memory 指令并编排读写删除。
- `SQLiteMemoryStore` 默认把 PREF/LTM 写入目标 repo 的 `.repopilot/memory.sqlite3`，使用 stdlib `sqlite3`，不依赖外部数据库。
- `repo_key` 通过 resolved repo path、POSIX 分隔符、Windows lower-case 和稳定 hash 生成；audit 不暴露本机绝对路径或 DB 路径。
- 支持 `记住: ...`、`请记住...`、`忘记: ...`、`请忘记...`、`remember: ...`、`forget: ...`，并兼容全角/半角冒号；`stm:` / `会话:` 写 STM，`pref:` / `偏好:` 写 PREF，`project:` / `项目:` 写 LTM。
- memory command 在 `RequestRouter` / keyword 路由前确认优先，不执行 `repo_rag`；普通 repo_search 可记录脱敏 memory summary。
- Memory audit 只保留在内部 trace，不进入 `/chat` 顶层字段或 `tool_calls`。

### Long Task Control Plane

- `LongTaskManager` 解析明确长任务指令，并在 memory command 之后、`RequestRouter` / keyword 路由前处理控制命令，避免 `task_xxx` 误触发 repo_search。
- `SQLiteLongTaskStore` 默认把任务状态写入目标 repo 的 `.repopilot/tasks.sqlite3`，复用 V13 repo_key 规范化规则：resolved path、POSIX 分隔符、Windows lower-case 和稳定 hash。
- 创建长任务只保存 deterministic task-type plan，不自动执行；显式 `恢复任务 task_xxx` 每次只推进一个 step。
- step action 只允许调用现有只读 `repo_rag`，且必须经过 `ToolRegistry`、`PermissionPolicy`、`ApprovalGate` 和 `ToolExecutor`。
- 支持 `paused`、`blocked`、`completed`、`failed`、reopen for retry、quota 和 archive；scratch 与 ReAct trace 只保存脱敏摘要。
- V14 只预留 subagent/worktree handoff metadata，不执行真实 subagent 调度或 git/worktree 操作。

### Assistant Control Surface

- 通过明确状态类 `/chat` 消息触发，例如 `助手状态`、`RepoPilot 状态`、`你能做什么`、`assistant status` 和 `what can you do`。
- AgentLoop 前置顺序为 Memory command、Long Task command、Assistant Control Surface、capability-status、repo_search/chat_only。
- 控制面只读聚合 Memory PREF/LTM/STM 计数和最近 Long Task 摘要，不隐式创建 `.repopilot/`、`memory.sqlite3` 或 `tasks.sqlite3`。
- 控制面请求不调用 `repo_rag`，不进入工具权限链路，不写 memory，不创建或推进任务。
- 控制面公开回答不泄露完整 memory value、scratch、ReAct trace、Evidence Pack、provider output、本机绝对路径或 DB 路径。

### Safe Patch Authoring

- 通过明确 patch 请求触发，例如 `请生成 patch 修改 app.py`。
- AgentLoop 前置顺序为 Memory command、Long Task command、Assistant Control Surface、Patch command / Patch intent、capability-status、repo_search/chat_only。
- Patch proposal 先通过现有 `repo_rag` / Evidence Pack 获取仓库证据，再由 Patch Authoring provider 生成结构化 proposal。
- 默认 fake Patch Authoring provider 保持离线确定性，不生成真实 diff；OpenAI-compatible provider 只有显式配置后才可返回结构化 diff。
- Pending patch 写入 repo-local `.repopilot/patches.sqlite3`，按 `user_id + repo_key` 隔离，默认 24 小时过期。
- Apply 只接受明确确认语法：`确认 patch <patch_id>`、`应用 patch <patch_id>`、`confirm patch <patch_id>`、`apply patch <patch_id>`。
- `patch_apply` 是 V16 唯一写入工具，必须经过 `ToolRegistry -> PermissionPolicy -> ApprovalGate -> ToolExecutor`，只写 diff 中的 repo 内相对路径。
- V16 不运行测试、不自动 commit、不创建 worktree、不执行 shell，不实现 Patch + Verify Loop。

### Patch + Verify Loop

- 通过明确组合确认触发，例如 `确认 patch <patch_id> 并运行验证`、`应用 patch <patch_id> 并运行 pytest`、`confirm patch <patch_id> and run verify`。
- 组合确认必须同时解析出 `patch_id` 和 verification label；缺失 label、半解析、非法 label、附加参数或 shell 语法时整体拒绝，不执行 `patch_apply`。
- 单独 `确认 patch <patch_id>` 仍保持 V16 apply-only 行为，不自动验证。
- apply 成功后才生成独立 `ToolInvocationContext(tool_name="verification_run", intent="verification_run", command_label=..., confirmed=True, scope_valid=...)` 并运行白名单验证。
- apply 失败、过期、hash mismatch、跨用户或跨 repo 时不运行验证。
- 验证失败只返回失败摘要和下一步建议；V18 不自动生成新 patch、不再次 apply、不持久化 verification result、不创建 worktree、不 commit/push。

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
  -> MemoryManager(STM/PREF/LTM command/read audit)
  -> LongTaskManager(command/status/step audit)
  -> AssistantControlSurface(read-only status)
  -> PatchManager(proposal/apply confirmation)
  -> PatchVerifyLoop(explicit apply+verify confirmation)
  -> VerificationRunner(whitelisted pytest/ruff/verify)
  -> QueryUnderstanding/SearchPlan -> QueryRewriteProvider
  -> ToolRegistry -> PermissionPolicy -> ApprovalGate
  -> ToolExecutor(repo_rag / patch_apply / verification_run) -> HybridRepoRetriever -> Reranker -> EvidencePack/ContextBudget
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
- `app/longtask/`：提供 Long Task parser、planner、repo-local SQLite store、manager 和 ReAct trace skeleton。
- `app/assistant/control_surface.py`：提供 Assistant Control Surface 触发词、只读状态聚合和 answer formatter。
- `app/patching/`：提供 patch 确认解析、Patch Authoring provider 边界、pending patch SQLite store、unified diff preflight/apply 和 Patch manager。
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

### V13：Memory

在 AgentLoop 中加入真实可用的轻量 Memory 边界。V13 使用 repo-local SQLite 保存 PREF/LTM，使用进程内 STM 保存 session 记忆，支持明确中英文 memory 指令和删除指令。Memory 指令通过现有 `answer` 字段返回确认，且不调用 repo_rag；普通请求只把脱敏 memory audit 写入内部 trace。

V13 保持 `/chat` 顶层响应 contract 不变。Memory 不提供向量召回、不做自动 LLM 总结、不参与 citation validation，也不能覆盖 repo evidence 对代码事实回答的约束。

### V14：Long Task / ReAct Skeleton

V14 在 AgentLoop 中加入 Long Task Control Plane。Memory command 和明确长任务指令均在 `RequestRouter` / keyword 路由前处理，顺序为 Memory command 先识别、Long Task command 后识别；创建、查看、列出、暂停、补充、归档和 reopen 控制命令不调用 `repo_rag`。显式 `resume/run` 每次只推进一个 step，并继续通过现有权限、审批和 `ToolExecutor(repo_rag)` 执行只读检索。

V14 使用 `.repopilot/tasks.sqlite3` 保存 `user_id + repo_key` 范围的任务状态、task-type plan、scratch 摘要和 ReAct trace 摘要。默认 planning 使用 deterministic templates；显式真实 provider 配置时可增强模板字段，失败时 fallback。V14 保持 `/chat` contract 不变，不新增 `/tasks` API，不执行后台任务、不创建 worktree、不调度真实 subagents、不执行 shell、不自动修改代码。

### V15：Assistant Control Surface

V15 在 AgentLoop 中加入只读 Assistant Control Surface。明确状态类消息通过现有 `/chat.answer` 返回当前能力、Memory 计数、Long Task 摘要和下一步命令建议；`related_files=[]` 且 `tool_calls=[]`。

V15 保持 `/chat` contract 不变，不新增公开 API 或顶层字段。控制面状态读取不调用 `repo_rag`、不写 memory、不创建任务、不执行 shell、不后台运行，也不隐式初始化 `.repopilot` 本地状态 DB。

### V16：Safe Patch Authoring

V16 在 AgentLoop 前段加入 Safe Patch Authoring。明确 patch 请求先通过 repo evidence 生成 patch proposal；合法 provider 输出会保存为 repo-local pending patch，并通过现有 `/chat.answer` 返回摘要、目标文件、patch id 和确认方式。

V16 保持 `/chat` contract 不变，不新增公开 API 或顶层字段。`patch_apply` 是唯一写入工具，必须在明确确认语法和有效 `ToolInvocationContext` 下通过 `PermissionPolicy` / `ApprovalGate`，并只修改 unified diff 中的 repo 内相对路径。V16 不运行测试、不自动 commit、不创建 worktree、不执行 shell。

### V17：Verification Runner

V17 在 AgentLoop 前段加入 Verification Runner。明确验证请求通过固定白名单标签触发：`pytest`、`ruff` 和 `verify`；`verify` 映射到 `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`。V17 不支持用户附加参数、targeted pytest、`ruff --fix`、管道、重定向或环境变量注入。

`verification_run` 注册为 `read_only=False`、`risk="write"`、`requires_approval=True`，只有有效 verification context 才能走 `ask -> ApprovalGate pass`，并通过 `ToolExecutor.verification_run(...)` 执行。runner 使用 argv list 和 `shell=False`，cwd 固定为 resolved `repo_path`，stdout/stderr 各最多 4000 字符，`/chat.answer` 验证输出摘要总计最多 6000 字符，并脱敏本机绝对路径、`.repopilot/...` 和常见 secret。V17 不自动串联 patch apply，不根据失败生成 patch，不持久化 verification result，不创建 worktree，不 commit/push。

### V18：Patch + Verify Loop

V18 在 AgentLoop Patch command 分支中加入明确组合确认处理，优先级为 `组合确认 > 纯 verification intent > capability-status/repo_search`。合法组合确认先执行 pending patch apply；只有 apply 成功后才创建独立 verification context 并运行 `pytest`、`ruff` 或 `verify` 白名单验证。

V18 保持 `/chat` contract 不变，组合结果只进入现有 `answer` 和安全 `tool_calls` 摘要。组合请求缺失验证标签、半解析、非法 label、附加参数或 shell 语法时整体拒绝，不 apply patch。V18 不持久化验证结果、不生成后续 patch、不创建 worktree、不 commit/push。

## 当前非目标

- 默认接入真实 LLM；真实 provider 仅作为显式配置的 OpenAI-compatible provider。
- 技能执行。
- SandboxRunner 实现。
- trace 持久化审计。
- 反思检查和 eval。
- 真实外部 embedding 服务、Milvus、Elasticsearch、PgVector、Qdrant。
- 真实 LLM query rewrite/rerank、向量 memory、自动 memory 总结和 context compression。
- 自动修改代码。
- shell 执行。
- 后台任务、自动循环执行、LLM 驱动自主多步规划。
- 多 agent orchestration。

## 工程化取向

RepoPilot 后续路线采用 lightweight industrial harness 取向：不是企业级平台，也不能停留在玩具 demo。默认继续使用 SQLite、文件、进程内状态和白名单命令等轻量实现，但每个阶段都应交付更真实的可用闭环，并保留权限、审批、审计、可恢复状态、验证和隔离等工业级边界。

- 清晰边界：Provider、Router、AgentLoop、ToolRegistry、ToolExecutor、Memory、RAG、Skill、Trace 分层明确。
- 可审计：每次 model/tool/skill/memory 调用都有结构化摘要，敏感内容默认不外泄。
- 可验证：每个阶段都有最小测试和 `scripts/verify.ps1` 入口。
- 可替换：RAG、Memory、Model Provider、向量库和存储都先做接口，默认实现保持轻量。
- 可交接：OpenSpec、harness、PROGRESS 和 HANDOFF 必须同步，不把关键项目知识只留在聊天里。

暂不追求：

- 一开始就引入复杂微服务、Kafka、Milvus、Elasticsearch、PostgreSQL 等重依赖。
- 一次性做完整企业级权限、观测、队列、分布式任务系统。
- 为了“看起来工程化”而增加个人维护不起的代码量。
- 直接实现完整工业 LLMGateway；后续只在真实模型调用需要时，增量吸收 timeout、fallback、脱敏 audit、轻量 retry、简单模型路由和成本摘要等小切片。

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

已归档至 V18：Patch + Verify Loop。当前无 active change。后续路线：

- V18：Patch + Verify Loop。串联明确组合确认下的 patch apply 和白名单 verify，返回失败摘要与下一步建议；不做持久恢复或 worktree。
- V19：Persistent Audit / Recovery。用轻量 SQLite 持久化关键 trace、patch attempt、verification result 和 task event，支持跨 session 恢复。
- V20：Worktree Isolation。在 patch/verify 成熟后引入受控 git worktree，隔离改动和验证，避免污染主工作区。

真实 subagents、connectors、notifications、heartbeat/cron 和 always-on assistant 放在 V20 之后单独规划；当前不要把这些写成已实现能力。
