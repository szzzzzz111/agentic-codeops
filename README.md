# RepoPilot

RepoPilot 是一个面向代码仓库分析任务的可控 Code Agent Harness，目标不是替代通用 AI IDE 或 AI 编程助手，而是围绕 Agent 的工具调用、安全边界、执行追踪、评测和交接机制，构建一个可验证、可审计、可扩展的代码智能体执行框架。当前应用场景包括代码仓库阅读、Bug 定位和修复建议。

当前实现包含 V1 Agent 服务入口、V2 安全只读仓库工具层、V3 最小确定性 Agent Loop、V4 Skill Metadata Loader、V5 Skill Content Loader、V6 Agent Harness Kernel + Router Kernel、V7 Permission + Approval Gate 和 V8 Query Understanding + Lexical Repo RAG。项目价值不在于“更会写代码”，而在于让 Agent 执行过程有明确边界、可观察输出和可交接规则。

## 当前能力与定位

- 提供 FastAPI 应用和 `POST /chat`，作为 Agent 服务入口。
- 请求字段包含 `user_id`、`session_id`、`message` 和 `repo_path`。
- 每次请求生成唯一 `trace_id`，响应保留 `related_files` 和 `tool_calls` 审计字段。
- `CodeAgent` 当前通过轻量 `AgentLoop` 执行最小确定性仓库搜索，不接真实 LLM。
- `RequestRouter` 将请求路由到 `repo_search` 或 `chat_only`。
- `ToolRegistry` 记录只读低风险工具元数据；`PermissionPolicy` 和 `ApprovalGate` 在工具调用前做 allow/deny/ask 决策。
- `QueryUnderstanding` 生成 deterministic `SearchPlan`，`ToolExecutor` 统一收口只读工具调用，当前包装 `search_code` 和 `repo_rag`。
- `TraceEvent` 在 Kernel 内部记录路由、权限、审批、工具调用、工具结果和拒绝事件；当前不作为 `/chat` 顶层字段返回。
- `related_files` 和 `tool_calls` 返回真实只读 lexical repo RAG 检索结果。
- 使用 OpenSpec specs、harness rules、review checklist、pytest 和 handoff 约束开发过程。
- 提供安全只读仓库文件工具：
  - `list_files(repo_path)`
  - `read_file(repo_path, file_path, max_chars=12000)`
  - `search_code(repo_path, keyword, max_results=20)`
- 提供 Skill Metadata Loader：
  - `load_skill_metadata(repo_path)`
  - 发现 `.agents/skills/*/SKILL.md`
  - 只解析 `name`、`description` 和相对仓库 `path`
- 提供 Skill Content Loader：
  - `load_skill_content(repo_path, skill_path)`
  - 按相对路径读取 `.agents/skills/<skill>/SKILL.md`
  - 返回 `path` 和完整 `content`
  - 不解析 frontmatter、不执行 skill
- V6 不执行 skill，不把 skill loader 接入 `/chat` 决策；Skill-aware Agent Loop 已降级为历史 draft 和后续 skill 子能力参考。

V8 当前只做 deterministic query understanding 和非向量化 lexical repo RAG，不做 embedding、向量库、LLM query rewrite、rerank 或 memory。

## 阶段说明

### V1：Agent 服务入口和可追踪请求结构

V1 的意义不是普通 mock 接口，而是建立可测试的 Agent 服务入口：

- `POST /chat`
- `ChatRequest` / `ChatResponse`
- `trace_id`
- `related_files` / `tool_calls` 响应字段
- pytest 接口测试

### V2：安全只读仓库工具层

V2 的意义不是普通文件读取，而是建立仓库访问安全边界：

- `list_files`
- `read_file`
- `search_code`
- `repo_path` 内部访问限制和路径逃逸防护
- 敏感文件、隐藏目录、忽略目录和二进制文件过滤
- 只读工具单元测试

### V3：统一工具执行边界

V3 的意义不是让 Agent 变聪明，而是把工具调用收口到 `ToolExecutor`：

- `CodeAgent` 通过 `ToolExecutor` 调用 `search_code`
- `/chat` 返回真实 `related_files`
- `/chat` 返回 `tool_calls` 摘要
- `tool_calls` 不包含完整文件内容、完整搜索结果或本机绝对路径
- 为后续 `SandboxRunner`、trace audit、eval 和 reflection 留出扩展点；`PermissionPolicy` 和最小 `ApprovalGate` 已在 V7 接入

### V4：Skill Metadata Loader

V4 的意义不是执行技能，而是建立 DeepAgents 风格的技能发现边界：

- 发现 `.agents/skills/*/SKILL.md`
- 读取 YAML frontmatter 中的 `name` 和 `description`
- 返回相对仓库路径 `path`
- 不读取或返回完整 skill 正文
- 不接入 `/chat` 决策
- 不执行 skill

### V5：Skill Content Loader

V5 的意义不是让 Agent 自动使用技能，而是在 metadata-first 之后提供 progressive disclosure 的按需读取层：

- 按相对仓库路径读取 `.agents/skills/<skill>/SKILL.md`
- 返回 `{"path": "...", "content": "..."}`
- 限制读取范围在 `.agents/skills/<skill>/SKILL.md`
- 拒绝路径逃逸、非 skill 文件、缺失文件和符号链接目录绕过
- 设置完整内容读取上限
- 不解析 frontmatter
- 不接入 `/chat` 决策
- 不执行 skill

### V6：Agent Harness Kernel + Router Kernel

V6 的意义不是扩展 skill-aware 行为，而是把现有搜索链路包进一个可演进的轻量 Harness Kernel：

- `AgentLoopRequest(message, repo_path, trace_id)` 作为 Kernel 输入 contract。
- `RequestRouter` 返回 `RouteDecision(route, keyword, reason)`，当前只支持 `repo_search` 和 `chat_only`。
- `ToolRegistry` 返回 `ToolSpec(name, description, read_only, risk)`，当前默认只允许只读低风险 `search_code`。
- `AgentLoop` 执行最小闭环：route -> registry gate -> `ToolExecutor.search_code` -> response。
- `TraceEvent` 在内部记录 `request_routed`、`tool_call`、`tool_result` 和 `tool_rejected`。
- `/chat` 顶层响应仍只返回 `answer`、`related_files`、`tool_calls`，不新增 trace 字段。
- 不实现 `ProviderAdapter`、`ContextBuilder`、`SkillRegistry` 或 `SessionStore` 运行时代码。

### V7：Permission + Approval Gate

V7 的意义不是开放高风险工具，而是在统一执行层加入确定性的权限和审批边界：

- `ToolSpec` 新增 `requires_approval`，默认 `search_code` 仍为只读、低风险且不需要审批。
- `PermissionPolicy` 产出 `allow`、`deny` 或 `ask`，优先级固定为 deny > ask > allow。
- `ApprovalGate` 只消费权限决策；V7 不实现真实审批 UI 或审批持久化。
- `deny` 和 `ask` 分支不调用 executor，`related_files` 和 `tool_calls` 均为空。
- 权限和审批审计仅记录在内部 `trace_events_internal`，不通过 `/chat` 暴露。
- `/chat` 顶层响应仍只返回 `answer`、`related_files`、`tool_calls`，不新增 trace 字段。

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

## 工程化取向

RepoPilot 后续路线要体现工程化味道，但不追求重型企业平台。由于当前主要由个人配合 AI 开发，工程化优先体现在：

- 清晰边界：Provider、Router、AgentLoop、ToolRegistry、ToolExecutor、Memory、RAG、Skill、Trace 分层明确。
- 可审计：每次 model/tool/skill/memory 调用都有结构化摘要，敏感内容默认不外泄。
- 可验证：每个阶段都有最小可验收测试和 `scripts/verify.ps1` 入口。
- 可替换：RAG、Memory、Model Provider、向量库和存储都先做接口，默认实现保持轻量。
- 可交接：OpenSpec、harness、PROGRESS 和 HANDOFF 必须同步，不把关键项目知识只留在聊天里。

暂不追求：

- 一开始就引入复杂微服务、Kafka、Milvus、Elasticsearch、PostgreSQL 等重依赖。
- 一次性做完整企业级权限、观测、队列、分布式任务系统。
- 为了“看起来工程化”而增加个人维护不起的代码量。

## 启动接口

```bash
uvicorn app.main:app --reload
```

接口地址：

```text
http://127.0.0.1:8000
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
  "answer": "已基于 lexical repo RAG 检索 `UNIQUE_BUG_TOKEN`，找到相关证据：app/example.py:1-3。",
  "related_files": ["app/example.py"],
  "tool_calls": [
    {
      "tool_name": "repo_rag",
      "keyword": "UNIQUE_BUG_TOKEN",
      "question_type": "code_location",
      "retrieval_mode": "lexical",
      "status": "success",
      "result_count": "1"
    }
  ]
}
```

## 运行测试

```bash
pytest
```

可选静态检查：

```bash
ruff check .
```

## 当前架构

```text
API -> ChatService(trace_id) -> CodeAgent -> AgentLoop
  -> QueryUnderstanding/SearchPlan
  -> ToolRegistry -> PermissionPolicy -> ApprovalGate
  -> ToolExecutor(repo_rag) -> LexicalRepoRetriever -> file_tools
```

- `app/main.py`：创建 FastAPI 应用并注册路由。
- `app/api/chat.py`：暴露聊天接口。
- `app/schemas/chat.py`：定义请求和响应模型。
- `app/services/chat_service.py`：创建请求级 `trace_id` 并编排智能体调用。
- `app/agents/code_agent.py`：调用轻量 AgentLoop 并适配 `/chat` 响应结构。
- `app/harness/kernel.py`：提供 RequestRouter、QueryUnderstanding 接入、ToolRegistry、PermissionPolicy、ApprovalGate、AgentLoop 和 TraceEvent 最小 Kernel。
- `app/rag/query_understanding.py`：提供 deterministic `SearchPlan`。
- `app/rag/repo_rag.py`：提供 repo chunk、lexical scoring、dedup 和 citation。
- `app/tools/tool_executor.py`：统一包装只读代码搜索、lexical repo RAG 和 skill loader 工具调用。
- `app/tools/file_tools.py`：提供安全仓库文件工具。
- `app/tools/skill_loader.py`：提供 Skill Metadata Loader 和 Skill Content Loader。
- `app/observability/tracing.py`：生成请求级 `trace_id`；当前不是完整持久化审计系统。

## 当前流程暂不包含

- 真实 LLM 接入。
- 技能执行。
- SandboxRunner 实现。
- trace 持久化审计。
- 反思检查。
- 评测。
- embedding、向量库、LLM query rewrite、rerank 或 context compression。
- Memory。
- 自动修改代码。
- shell 执行。
- 复杂智能体循环、LLM 驱动语义理解和多步规划。

## 文件工具安全边界

V2 文件工具是只读工具，不执行 shell 命令。它们会把访问限制在 `repo_path` 内，拒绝路径穿越，跳过忽略目录，过滤 `.env` 和私钥等敏感文件，忽略二进制文件，并限制读取和搜索返回规模。

## 后续安全架构

V2 提供的是工具级安全边界，不是完整的权限系统、沙箱系统或人工审批流。这是有意为之，因为当前工具只读；V3 已经通过 `ToolExecutor` 把 `search_code` 接入 `/chat`，后续高风险能力仍必须继续经过统一执行层扩展。

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

这样可以把后续安全能力做成增量扩展，而不是重写现有代码。权限检查、人工介入审批、工具调用审计和沙箱命令执行都应该围绕 `AgentLoop` / `ToolExecutor` 边界实现，不应该散落在 `main.py`、API handler 或具体工具函数里。

已实现和建议演进：

- V3 已实现：让 `CodeAgent` 通过轻量 `ToolExecutor` 调用只读 `search_code`。
- 后续：为每次工具调用增加 trace 和审计记录。
- V7 已实现轻量 `PermissionPolicy` 和最小 `ApprovalGate`，当前只做确定性 allow/deny/ask 边界。
- 后续：在写文件、运行命令、提交代码或创建 PR 等高风险动作前接入真实审批流程。
- 后续：仅为执行命令类工具增加 `SandboxRunner`，例如测试运行器。

## 路线图

- V2：加入安全仓库工具：`list_files`、`read_file` 和 `search_code`。
- V3：加入简单规则型智能体循环和统一 `ToolExecutor`。
- V4：加入基于 markdown 的 Skill Metadata Loader。
- V5：加入 Skill Content Loader / progressive disclosure，按需读取完整 `SKILL.md`。
- V6：Agent Harness Kernel + Router Kernel，已建立 RequestRouter、ToolRegistry、AgentLoop、TraceEvent 和最小数据 contract；Provider/Context/Skill/Session runtime 后移。
- V7：Permission + Approval Gate，已把工具风险等级、允许/拒绝/询问策略和内部审计事件接入统一执行层；不在 `/chat` 暴露 trace。
- V8：Query Understanding + Lexical Repo RAG，已实现 deterministic 检索前理解、repo-local chunk、lexical scoring 和 citation。
- V9：Embedding Retrieval + Hybrid Search，补 embedding provider、可替换检索接口和 hybrid fusion；Milvus/ES 暂不默认引入。
- V10：Query Rewrite / Rerank / Grounded Answer / Context Budget，引入 LLM query rewrite、rerank、证据约束回答和上下文预算。
- V11：Memory，区分 STM、LTM 和 PREF，并加入 memory audit。
- V12：Long Task / ReAct / Subagents，支持计划、任务状态、pause/resume、scratch space、subagents 和 worktree handoff。
- V13：Personal Assistant Gateway，探索 always-on、heartbeat/cron、connector、通知和人工审批。

## V8 Update: Query Understanding + Lexical Repo RAG

V8 已将旧路线里的“大 Repo RAG Engineering”收窄为可落地的非向量化 repo-local RAG 骨架。当前主链路为：

```text
API -> ChatService(trace_id) -> CodeAgent -> AgentLoop
  -> QueryUnderstanding/SearchPlan
  -> ToolRegistry -> PermissionPolicy -> ApprovalGate
  -> ToolExecutor(repo_rag) -> LexicalRepoRetriever -> file_tools
```

V8 当前实现：

- deterministic `QueryUnderstanding`，生成 `SearchPlan`，包含 `question_type`、`keywords`、`symbols`、`path_hints`、`max_results` 和 `retrieval_mode=lexical`。
- repo 文本 chunk，chunk 包含 `chunk_id`、`file_path`、`start_line`、`end_line` 和 `text`。
- lexical scorer，按 keyword、symbol、path、filename 和 exact token bonus 排序。
- citation 输出，`related_files` 来自 citation 文件路径。
- `/chat` 顶层响应字段仍为 `trace_id`、`answer`、`related_files`、`tool_calls`。

V8 仍不包含 embedding、Milvus、Elasticsearch、PgVector、Qdrant、LLM query rewrite、rerank、memory、context compression、真实 LLM、shell、写文件工具、SandboxRunner、skill execution 或多 agent orchestration。

路线重排：V9 为 Embedding Retrieval + Hybrid Search；V10 为 Query Rewrite / Rerank / Grounded Answer / Context Budget；V11 为 Memory；V12 为 Long Task / ReAct / Subagents；V13 为 Personal Assistant Gateway。
