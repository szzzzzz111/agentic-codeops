# 架构说明

本文只把当前实现描述为 current architecture。阶段为何引入、当时如何验证以及旧路线的完整叙事，
以 archived OpenSpec changes 和 Git history 为准；不能从历史设计反推当前 runtime capability。

## 系统上下文

RepoPilot 是一个本地 Coding Agent Harness：用户通过 HTTP `/chat` 或薄 CLI 提交仓库理解、受控 patch、
验证和 worktree lifecycle 请求；RepoPilot 在 repository scope 内完成 deterministic routing、权限/审批判断、
工具执行、脱敏 audit 和 fail-closed 状态管理。默认测试和 CI 不依赖网络或真实模型。

```text
User / local CLI
  -> FastAPI /chat
  -> ChatService(trace_id)
  -> CodeAgent
  -> AgentLoop
       -> command/control routes
       -> ToolRegistry -> PermissionPolicy -> ApprovalGate -> ToolExecutor
       -> repo-local managers and stores
  -> ChatResponse(trace_id, answer, related_files, tool_calls)
```

边界外部包括被分析的 Git repository、可选 OpenAI-compatible model endpoint，以及 development-time
OpenSpec/Harness/reviewer/controller。后者不属于 RepoPilot runtime，也不能仅因仓库中存在配置、skills 或
validator 就被写成产品能力。

## 当前请求路由

`AgentLoop._run_inner()` 使用确定性优先级处理请求。高优先级明确命令不会落入普通 repo search：

1. Memory command；
2. Long Task command，只有显式推进的 repo evidence step 可调用 `repo_rag`；
3. Assistant status；
4. worktree inventory、inspection、disposal/reconciliation、verified promotion、re-verification；
5. Patch + Verify 组合确认、单独 patch apply 确认、patch proposal；
6. standalone verification；
7. persistent audit recovery；
8. `RequestRouter` 的 capability status、repo search 或 chat-only fallback。

普通仓库问答主链路为：

```text
RequestRouter(repo_search)
  -> QueryUnderstanding / SearchPlan
  -> ToolRegistry -> PermissionPolicy -> ApprovalGate -> ToolExecutor(repo_rag)
  -> QueryRewriteProvider
  -> LexicalRepoRetriever + EmbeddingRepoRetriever
  -> HybridRepoRetriever -> Reranker
  -> EvidencePack / ContextBudget
  -> GroundedAnswerGenerator -> ModelProvider
  -> citation validation / conservative fallback
```

Lexical/path/symbol evidence 是可审计主基线；deterministic embedding、rewrite 和 rerank 只辅助召回与排序。
Public response 继续只返回 `trace_id`、`answer`、`related_files`、`tool_calls`，内部 Evidence Pack、prompt、
完整 provider output、absolute path 和 secret 不进入公开 schema。

## 模块与代码映射

| 责任 | 当前入口 | 边界 |
|---|---|---|
| 应用装配 | `app/main.py` | 创建 FastAPI 并注册 router，不写业务逻辑 |
| HTTP contract | `app/api/chat.py`、`app/schemas/chat.py` | 只处理 `/chat` request/response |
| 请求级编排 | `app/services/chat_service.py` | 创建 trace 并调用 CodeAgent |
| Agent adapter | `app/agents/code_agent.py` | 适配 AgentLoop result 到 public response |
| 核心路由与 gate | `app/harness/kernel.py` | command priority、ToolRegistry、PermissionPolicy、ApprovalGate |
| Runtime capability facts | `app/harness/capabilities.py` | 从已注册 tools 推导可声明能力，不读路线文档 |
| 安全文件访问 | `app/tools/file_tools.py` | repo scope、path traversal、敏感/二进制过滤 |
| 统一工具执行 | `app/tools/tool_executor.py` | repo RAG、worktree create/dispose、patch apply、verification |
| 检索与证据 | `app/rag/` | query understanding、rewrite、hybrid retrieval、rerank、Evidence Pack |
| Grounded answer/provider | `app/answering/`、`app/providers/` | evidence-only generation、citation validation、默认 fake provider |
| Patch lifecycle | `app/patching/` | proposal、pending store、confirmation、controlled diff validation/apply |
| Verification | `app/verification/runner.py` | 固定 `pytest`、`ruff`、`verify` labels，禁止任意 shell |
| Worktree lifecycle | `app/worktrees/manager.py` 与 `app/worktrees/` | create、inspect、reverify、dispose、promotion preflight |
| Mutation serialization | `app/locks/repo_mutation.py` | 同 repo 的 RepoPilot-owned 写风险路径串行化 |
| Memory/Long Task | `app/memory/`、`app/longtask/` | repo-local scoped state；不替代 repository evidence |
| Audit/trace | `app/audit/`、`app/observability/` | redacted persistent summary 与 request-local trace |
| Local CLI | `app/cli.py` | 映射到既有 ChatService，不创建第二套 runtime |

## 状态与信任边界

Repo-local 状态位于被分析仓库的 `.repopilot/`，并按 `user_id + normalized repo_key` 或相应 lifecycle scope
隔离。Public response 和 audit 都不得泄漏数据库路径、原始 diff、完整 stdout/stderr、Evidence Pack、prompt、
provider output、API key 或本机绝对路径。

| 状态 | Owner | 关键限制 |
|---|---|---|
| PREF/LTM memory | `SQLiteMemoryStore` | STM 仅进程内；memory 不能替代 citation evidence |
| Long Task | `SQLiteLongTaskStore` | 创建不自动执行；显式 resume 每次最多推进一步 |
| Pending patch | patch store | scope、expiry、hash、citation、path 和 diff 校验后才可确认 |
| Persistent audit | audit store | 只保存脱敏摘要；audit failure 不破坏主要回答 |
| Worktree lifecycle | worktree store | user/repo scope、Git registry/path/base 一致性、明确状态迁移 |
| Mutation lock | repo mutation lock store | 同 repo 写风险互斥；conflict/unavailable fail closed |

写风险工具统一经过 `ToolRegistry -> PermissionPolicy -> ApprovalGate -> ToolExecutor`。当前 `ApprovalGate`
只消费 request context 内的确定性决策，不证明持久化 Operator authority；request-supplied `user_id` 也不能
单独证明真实人工身份。

## 写入与验证闭环

```text
explicit patch request
  -> repository evidence
  -> validated pending patch proposal
  -> explicit confirmation
  -> repo mutation lock
  -> detached locked worktree create
  -> controlled patch_apply(stored diff)
  -> optional whitelisted verification
  -> inspect / reverify / dispose-or-reconcile
  -> explicit verified promotion to clean matching main workspace
  -> redacted lifecycle and audit summary
```

- Worktree 内容是隔离执行和完整性证据；verified promotion 的写入源仍是 stored controlled patch。
- Promotion 要求 scoped lifecycle、clean main workspace、matching base HEAD、Git/worktree metadata 与 patch hash
  一致，并通过 existing permission/approval/tool boundary。
- Verification 只接受 `pytest`、`ruff`、`verify` 三个 label，使用当前 `sys.executable -I`、固定 cwd、
  controlled environment、bounded output 和 secret/path redaction；required tool 缺失时明确失败。
- Runtime 不自动 commit、merge、push、建 branch/PR、删除任意 worktree、prune、修复失败或重试。

## 运行时约束与非目标

- API layer 不直接读 repository files、运行 subprocess 或实现 Agent decisions。
- Managers 负责各自 scope/lifecycle；ToolExecutor 负责统一执行，不承载开放式业务推理。
- Repo search 保持 grep-first、RAG-assisted；不默认接外部 vector DB、embedding service 或模型下载。
- 默认 provider 为 local deterministic fake。真实 OpenAI-compatible provider 只有显式配置才进入 grounded
  answer/部分 planner boundary；默认 AgentLoop 不因环境变量自动启用真实 patch diff generation。
- 当前不实现真实审批 UI/持久 authority、SandboxRunner、后台任务、durable execution、runtime subagents、
  connectors、notifications、heartbeat/cron、自动 repair 或产品内 Git delivery。
- Development workflow 的 OpenSpec、Harness、skills、review receipts、authority validator 和 dormant replay
  只约束 repository development，不进入 `/chat` runtime contract。

## 历史与规格入口

- 长期 normative requirements：`openspec/specs/`。
- 阶段 proposal/design/tasks、当时验证与决策：`openspec/changes/archive/`。
- Acceptance-oriented inventory：`docs/FEATURE_LIST.json`。
- Durable status、remaining debt、候选顺序和阶段索引：`docs/PROGRESS.md`。
- 实时 branch、HEAD、worktree、active change 和 remote state：Git/OpenSpec commands，不以本文为证据。

下面保留旧版逐阶段补充作为迁移期可折叠参考；它不是 current truth，后续可在不丢失唯一证据的前提下移除。

<details id="architecture-history">
<summary>旧版逐阶段架构补充（历史参考）</summary>

## Repo Mutation Locking

当前写风险路径在进入 mutable preflight / execution 前会尝试获取 repo-key scoped
mutation lock：ordinary patch apply、组合 Patch + Verify、retained worktree
re-verification、worktree disposal/reconciliation、verified patch promotion 和 standalone
verification。锁按 normalized `repo_key` 跨 user 串行同仓库 RepoPilot-owned mutation；
业务 eligibility 仍按 `user_id + repo_key` 校验。

锁 conflict 或 unavailable 时 fail closed，并通过现有 `/chat.answer` 返回安全摘要，不新增
`/chat` 顶层字段。read-only inventory/inspection、audit recovery、capability/status、
memory/task status 和 repo search 不获取 mutation lock。该能力不实现 scheduler、queue、
后台 retry、automatic repair、commit/merge/push、branch/PR automation、connector、
notification 或 `git worktree prune`。

### Historical reference: Verified Patch Promotion (V25)

V25 当前链路为 `AgentLoop -> repo mutation lock -> scoped promotion preflight -> ToolRegistry -> PermissionPolicy ->
ApprovalGate -> ToolExecutor.patch_apply(main workspace, stored patch) -> lifecycle/audit summary`；路由在 V23 disposal/reconciliation 后、V22 re-verification 前，只接受精确确认命令。

Preflight 要求当前 `user_id + repo_key`、`verification_succeeded` + `applied_in_worktree`、主工作区干净、主 `HEAD == base_commit`、Git/worktree ownership/registry/lock 一致，以及 stored patch hash 与 retained worktree 内容和受控 patch 预期一致。worktree 内容只作完整性证据，不是写入源。promotion 专用 `patch_apply` 使用固定 argv 的 Git atomic apply；patch/worktree/journal 的 `promoted` 终态通过 SQLite cross-database transaction 一起提交。状态同步失败时以受控逆向 patch 回滚主工作区。V25 不 commit、merge、push、建分支/PR、删除 worktree、prune、后台重试或自动修复。

### Historical reference: Worktree Disposal / Reconciliation (V23)

V23 当前实现链路为
`AgentLoop -> scoped disposal/reconciliation preflight -> ToolRegistry -> PermissionPolicy ->
ApprovalGate -> ToolExecutor.worktree_dispose -> lifecycle/audit summary`。

V23 route 位于 inventory/inspection 之后、V22 re-verification 之前；共享 Git metadata
runner 的独立 timeout 与读取前硬上限属于 destructive disposal 开放前的 blocking 工作。V23
只允许明确 confirmed disposal 与安全残缺集 reconciliation，不执行 promotion、隐式修复、自动重试
或 `git worktree prune`。

### Historical reference: Worktree Re-verification (V22)

V22 当前链路为
`AgentLoop -> scoped fail-closed worktree preflight -> ToolRegistry -> PermissionPolicy ->
ApprovalGate -> ToolExecutor.verification_run(retained worktree) -> lifecycle/audit summary`。

Preflight 只核对 scoped metadata、expected directory、Git registry/path 与 HEAD/base，
不执行 V21 完整 diff/preview inspection。任一一致性失败均不运行 verification、不修复、
不 reconcile、不 cleanup、不重试，并保留原 lifecycle。实际执行成功/失败只复用
`verification_succeeded` / `verification_failed`；patch 始终保持
`applied_in_worktree`。每次识别出的请求通过 related-to-worktree 的脱敏
`verification_result` audit 表达 attempt 与 rerun 次数。

V22 preflight 只允许 `patch_applied`、`verification_failed`、`verification_succeeded`
lifecycle。内部 `execution_repo_path` 不存入 DB，而是从 resolved repo root、固定
`.repopilot/worktrees` managed root 与 scoped worktree id 动态重建。

### Historical reference: Worktree Inventory / Inspection (V21)

V21 已实现、完成 internal/external review、提交、归档、合并并推送。当前链路为
`AgentLoop -> WorktreeManager(read-only inventory / inspection) -> fixed Git argv /
readonly SQLite -> bounded safe formatter -> /chat.answer`。

V21 inspection 替代 V20 narrow status 行为；preview 路径只来自机器可解析
`git diff --name-only -z` 输出，diffstat 来自 `--numstat -z`，untracked 只报告 count。
`AgentLoop.run()` 统一 wrapper 保持不变，`_skip_persistent_audit_for_result()` 通过
`worktree_inventory` / `worktree_inspection` 事件跳过 persistent audit，保证读取不创建
或修改状态。

所有 public metadata scalar 和 tracked changed-file 摘要经过统一 bounded formatter；
tracked path 最多展示 20 条并报告 omitted count。Git inspection 设置
`GIT_OPTIONAL_LOCKS=0`，worktree SQLite 读取使用 `mode=ro&immutable=1`；损坏 store
和 Git 错误安全降级为 empty/not-found/partial，不执行修复或写入。

### Historical reference: Worktree Isolation (V20)

V20 将 RepoPilot 产生的 patch 写入从主仓库当前 `HEAD` 创建的 detached、locked
Git worktree：

```text
AgentLoop
  -> PatchManager.prepare_apply(original repo scope)
  -> ToolRegistry -> PermissionPolicy -> ApprovalGate
  -> ToolExecutor.worktree_create -> WorktreeManager
  -> ToolExecutor.patch_apply(execution_repo_path)
  -> optional ToolExecutor.verification_run(execution_repo_path)
  -> PatchManager / WorktreeManager / AuditManager(original repo-local stores)
```

`execution_repo_path` 仅在当前调用栈内部传播，不进入 `/chat`、`tool_calls`、SQLite
或 persistent audit。原始 `request.repo_path` 继续承担 patch/worktree/audit scope
与 repo identity。standalone verification 继续使用原始工作区。

`WorktreeManager` 负责 Git 前置检查、固定 argv 创建、失败回滚、生命周期状态和只读
查询。成功创建的 worktree 在 V20 保留并锁定；V25 只允许严格验证后的 promotion，清理、commit、merge、push
与继续执行均不属于该创建流程。

RepoPilot 当前采用渐进式 Harness 架构。目标不是替代通用 AI IDE 或 AI 编程助手，而是围绕代码仓库分析任务，把 Agent 的工具调用、安全边界、执行追踪、验证和交接机制做成可控、可审计、可扩展的执行框架。

## 当前主链路

```text
API -> ChatService(trace_id) -> CodeAgent -> AgentLoop
  -> MemoryManager(STM/PREF/LTM command/read audit)
  -> LongTaskManager(command/status/step audit)
  -> AssistantControlSurface(read-only status)
  -> PatchManager(proposal/apply confirmation)
  -> RepoMutationLockStore(repo-key scoped mutation guard)
  -> WorktreeManager(scoped create / inventory / inspection / disposal / re-verification / promotion preflight)
  -> PatchVerifyLoop(explicit apply+verify confirmation)
  -> VerificationRunner(whitelisted pytest/ruff/verify)
  -> AuditManager(persistent redacted audit / read-only recovery)
  -> QueryUnderstanding/SearchPlan -> QueryRewriteProvider
  -> ToolRegistry -> PermissionPolicy -> ApprovalGate
  -> ToolExecutor(repo_rag / worktree_create / patch_apply / verification_run) -> HybridRepoRetriever -> Reranker -> EvidencePack/ContextBudget
     -> GroundedAnswerGenerator -> ModelProvider
     -> LexicalRepoRetriever + EmbeddingRepoRetriever -> file_tools
```

- API 层只接收请求并返回响应。
- `ChatService` 负责编排请求、生成 `trace_id`、调用智能体。
- `CodeAgent` 负责调用轻量 `AgentLoop` 并适配 `/chat` 响应结构。
- `MemoryManager` 负责明确 memory 指令、repo-local SQLite PREF/LTM、进程内 STM 和脱敏 memory audit。Memory command 在 `RequestRouter` / keyword 路由前识别。
- `LongTaskManager` 负责明确长任务指令、repo-local SQLite task store、deterministic task-type plan、pause/resume、scratch 摘要和 ReAct trace skeleton。Long Task 控制命令在 memory command 之后、`RequestRouter` / keyword 路由前处理；只有显式 resume/run 当前 step 才能调用只读 `repo_rag`。
- `AssistantControlSurface` 负责明确状态类请求的只读聚合，返回当前能力、Memory 计数、Long Task 摘要和下一步命令建议。它在 Memory command 和 Long Task command 之后、Patch/Verification/Audit Recovery 之前处理，不调用 `repo_rag`，不写 memory/tasks 状态；V19 为所有 `/chat` 请求写入轻量 persistent audit trace envelope。
- `PatchManager` 负责明确 patch proposal 请求和明确 patch apply 确认。Proposal 先走 repo evidence；apply 只接受 `确认 patch <patch_id>` / `应用 patch <patch_id>` 等明确语法，并在权限检查前生成已归一化 `ToolInvocationContext`；写入路径由 `AgentLoop` 先获取 repo mutation lock。
- `PatchVerifyLoop` 负责明确组合确认请求，例如 `确认 patch <patch_id> 并运行验证`。组合确认在 Patch command 分支内优先于纯 Verification intent 处理；请求必须同时包含 patch id 和白名单 verification label，半解析或不安全 label 会整体拒绝且不 apply。
- `VerificationRunner` 负责明确验证请求、固定白名单标签、输出截断和脱敏。它在 Patch command / Patch intent 之后、capability-status / repo_search 之前处理，只允许 `pytest`、`ruff` 和 `verify`，并通过 `verification_run` 权限/审批边界执行。
- `AuditManager` 负责 V19 repo-local `.repopilot/audit.sqlite3` 持久审计与只读恢复。它记录脱敏 trace、patch attempt、verification result 和 long task event 摘要；recovery/status intent 在 patch/verification 之后、capability-status/repo_search 之前处理，命中后不调用 `repo_rag`，不执行 patch、verification、task resume 或 repo mutation。
- `QueryUnderstanding` 负责 deterministic 检索前理解，产出 `SearchPlan`。
- `QueryRewriteProvider` 负责 bounded deterministic multi-query rewrite，默认生成 `original` 和最多 3 条 Code Evidence variants。
- `ToolExecutor` 统一收口工具执行，当前包装只读 `search_code`、`repo_rag`、受控 `worktree_create`、受控写入 `patch_apply` 和受控验证 `verification_run`；写风险执行依赖上游 lock provenance 与 permission context。
- `LexicalRepoRetriever` 负责 repo-local chunk、lexical scoring、dedup 和 citation。
- `EmbeddingRepoRetriever` 使用本地确定性 embedding provider 对 repo chunk 做轻量 embedding retrieval。
- `HybridRepoRetriever` 负责合并 lexical 与 embedding retrieval 结果。
- `Reranker` 负责在 Evidence Pack 前对 merged retrieval results 做 deterministic rerank，并最多选择 `SearchPlan.max_results` 条结果。
- `EvidencePack` / `ContextBudget` 在 retrieval 后生成内部证据输入层和字符级预算摘要。
- `GroundedAnswerGenerator` 只消费预算内 included evidence，并负责 provider 调用、citation 校验、fallback 和脱敏 audit 摘要。
- `ModelProvider` 默认使用本地 deterministic fake provider；显式配置后可调用 OpenAI-compatible
  provider。共享 request 默认使用 `grounded_text`，结构化调用必须由 Planner/Patch 显式提供
  `json_object` instruction，Provider 不按 `question_type` 推断业务 schema。
- `file_tools` 提供安全仓库文件工具，不处理 HTTP 或 Agent 决策。
- Trace 贯穿请求生命周期，由 `ChatService` 创建请求级唯一 `trace_id`，并随 `/chat` 响应返回。V19 `AuditManager` 持久化脱敏 trace envelope 和关键事件摘要；完整 raw internal trace、hybrid retrieval channel detail、Evidence Pack content 和 provider content 不持久化，也不作为 `/chat` 顶层字段暴露。

当前 `/chat` 已通过 hybrid repo RAG 与 grounded answer 边界返回带 citation 的证据约束回答，并支持 repo-local SQLite-backed Memory 指令、Long Task Control Plane、Assistant Control Surface、Safe Patch Authoring、Verification Runner、Patch + Verify Loop、Persistent Audit / Recovery、Repo Mutation Locking 和 V20-V25 worktree 生命周期。Assistant Control Surface 只读聚合状态并通过现有 `answer` 返回；Safe Patch Authoring 通过现有 `answer` 返回 patch proposal / apply 结果；Verification Runner 与 Patch + Verify Loop 通过现有 `answer` 返回白名单验证或组合执行摘要；Persistent Audit / Recovery 记录脱敏事件摘要并通过现有 `answer` 返回只读恢复状态；Repo Mutation Locking 只序列化同 repo 的 RepoPilot-owned 写风险路径，不改变公开响应 schema；Worktree Isolation 把 standalone patch 与组合 Patch + Verify 放入 detached、locked worktree，不新增 API 或 `/chat` 顶层字段；Verified Patch Promotion 只在精确确认后把已验证 retained worktree 的 stored controlled patch 通过 approval-gated `patch_apply` 提升到主工作区。默认不接真实 LLM、不执行任意 shell、不自动 commit；显式环境配置只会把 OpenAI-compatible provider 接入 grounded answer 和 Long Task planner。共享 provider 可选记录 request-local latency、finish reason、model/fingerprint 和 token usage，但这些 metrics 不进入业务结果、公开响应或持久化 audit。`ModelPatchAuthoringProvider` 当前仅可通过依赖注入用于测试或自定义装配，默认 `AgentLoop` 不会因环境变量配置而启用真实 patch diff generation。

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
- V15 Assistant Control Surface 只能聚合状态和建议命令，不能替代 repo evidence 或 citation validation。
- V16 Safe Patch Authoring 的 proposal 必须先使用 repo evidence；provider diff 必须通过 schema、citation、路径和 diff 校验后才能创建 pending patch。
- V17 Verification Runner 不改变检索链路；验证请求不调用 `repo_rag`，不生成 Evidence Pack，也不影响 grep-first RAG baseline。
- 不默认引入 Milvus、Elasticsearch、PgVector、Qdrant 或重型 embedding cache；只有后续 repo 规模和任务类型明确需要时再通过单独阶段评估。

### Historical reference: 安全只读仓库工具层（V2）

V2 新增安全只读文件工具：

```text
app/tools/file_tools.py
```

包含：

- `list_files(repo_path)`
- `read_file(repo_path, file_path, max_chars=12000)`
- `search_code(repo_path, keyword, max_results=20)`

这些工具限制访问在 `repo_path` 内，拒绝路径逃逸，跳过敏感文件、隐藏目录、忽略目录和二进制文件。V3 当前已经通过 `ToolExecutor` 把 `search_code` 接入 `/chat`。

### Historical reference: ToolExecutor 执行层（V3）

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
- 控制面之外的 always-on assistant、notifications、heartbeat 或 cron。
- 自动修改代码。
- 沙箱执行命令。
- SandboxRunner 的实际实现。
- 真实审批 UI 或审批持久化。
- 完整 raw trace 持久化、trace replay 或自动恢复执行；V19 只提供脱敏审计摘要和只读 recovery/status。

### Historical reference: Query Understanding + Lexical Repo RAG (V8)

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

## Worktree Lifecycle 架构摘要

V9 已完成 Embedding Retrieval + Hybrid Search：补 embedding provider 边界、轻量默认实现、repo-local embedding retrieval 和 hybrid fusion，同时保留 V8 lexical retrieval 作为一等通道。当前路线进一步明确为 grep-first, RAG-assisted：lexical/path/symbol evidence 是可审计强基线，embedding/hybrid 只作为辅助召回通道。V9 不默认引入 Milvus、Elasticsearch、PgVector、Qdrant、真实外部 embedding 服务或模型下载。

V10 已完成 Evidence Pack + Context Budget；V11 已完成 Grounded Answer / Model Provider Boundary；V12 已完成 Query Rewrite + Rerank；V13 已完成 Memory；V14 已完成 Long Task / ReAct Skeleton；V15 已完成并归档 Assistant Control Surface；V16 已归档 Safe Patch Authoring；V17 已完成 Verification Runner；V18 已完成 Patch + Verify Loop；V19 已完成并归档 Persistent Audit / Recovery；V20-V25 worktree 生命周期能力已完成并归档。

V20 只实现受控 worktree 创建、隔离 patch/组合验证、生命周期状态和只读查询；V21-V25 逐步补齐 inventory/inspection、re-verification、disposal/reconciliation 和 verified promotion。commit、merge、push、branch/PR automation、runtime subagents、connectors、notifications 和 always-on assistant 仍须通过后续独立 OpenSpec change、harness 边界和 review 才能进入 runtime。

Worktree lifecycle 的稳定边界是：只读检查、白名单验证、不可逆清理和主工作区写入分别由独立阶段引入；每个写入阶段继续经过 repo mutation lock、`PermissionPolicy -> ApprovalGate -> ToolExecutor`，并保持明确命令、scope 校验、脱敏 persistent audit 和 fail-closed 失败语义。后续 Operator Control、Durable Execution、Background Worker、runtime subagents、connectors 和 notifications 仍只是候选方向；不得在没有独立 OpenSpec change 和 Harness review 前写成 runtime 能力。

### Historical reference: Embedding Retrieval + Hybrid Search (V9)

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

### Historical reference: Evidence Pack + Context Budget (V10)

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

### Historical reference: Grounded Answer + Model Provider Boundary (V11)

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
- `OpenAICompatibleModelProvider` 只在显式环境变量配置后启用，使用 `httpx` 调用 chat completions
  兼容接口。`REPOPILOT_MODEL_THINKING=disabled` 会显式发送关闭 thinking 的 provider 扩展；未配置
  时不发送该字段，其他值 fail closed。
- 共享 request 默认使用 `grounded_text`；`json_object` 必须携带调用方定义的名称、JSON object
  example 和 `1..16384` output token 上限，并在 HTTP 前完成基础校验。
- Provider 对 JSON mode 只校验非空、合法且顶层为 object；Long Task/Patch 分别负责自己的业务
  schema、step、citation、路径与 diff 校验。
- `stop` 视为正常完成；`length`、`content_filter`、`tool_calls` 与
  `insufficient_system_resource` fail closed。缺失或未知 finish reason 只标记 metrics 状态，以
  保留 OpenAI-compatible 端点兼容性。
- provider 输出必须引用 provided evidence citation，格式为 `relative/path.py:start-end`；无 citation、越界 citation、provider error 或 timeout 均返回保守 fallback。
- Grounded-text system instruction 会按 request evidence 的稳定顺序列出允许的 citation
  labels，要求模型至少逐字复制一个完整 `path:start-end` label，不得改写范围或创建新 citation；
  evidence text 被明确视为不可信仓库数据，不能覆盖 system instruction。
- Grounded-text user message 使用不带方括号的 citation label，并把 evidence items 放入明确标记
  为不可信数据的 JSON envelope；system instruction 禁止遵循、复述、转换或编码 evidence 内要求
  改变回答行为、泄露内容或输出 marker/token 的指令。`json_object` mode 保留原有 prompt assembly。
- Grounded-text instruction 还要求静默忽略命令、角色、策略、声明式 response rule 和额外输出要求；
  不得在回答、澄清、拒答或安全说明中确认、解释拒绝、转换或复现 original query 未明确询问的
  marker/token。若相同字符串是用户明确询问的仓库事实或标识符，仍可只基于相关 evidence 回答。
- 每个 grounded response（包括回答、澄清或拒答）必须以一个裸 allowed citation label 作为唯一
  最后一行；footer 不得包含前缀、markdown、包装符号、bullet、标点或额外文本。Provider 不自动
  补写 citation，模型不服从时仍由 validator fail closed。
- provider audit 只记录 provider name、model、status、error class 或 fallback reason，不记录完整
  prompt、完整模型输出、完整 Evidence Pack、API key、本机绝对路径、system fingerprint 或 token
  明细；response-local metrics 不穿透 Grounded Answer、Planner 或 Patch 业务结果。
- `/chat` 顶层响应仍只要求 `trace_id`、`answer`、`related_files` 和 `tool_calls`；provider audit 不进入 `tool_calls`。
- V11 不实现 query rewrite、rerank、memory、context compression、SandboxRunner、skill execution 或多 agent orchestration。

## 后续设计备忘：轻量 LLM Gateway

外部 LLMGateway 资料中的“稳定性控制面”概念对 RepoPilot 有参考价值，但本项目不应直接复制重型工业网关。当前已实现的是 V11 Model Provider Boundary，不是完整 LLMGateway：它只收口 provider 调用、环境变量配置、基础 timeout、错误 fallback、citation validation 和脱敏 provider audit。

后续如果增强真实模型调用，RepoPilot 应优先吸收轻量子集：

- 模型调用统一入口：继续围绕 `ModelProvider` / `GroundedAnswerGenerator`，不要让 API handler、AgentLoop 或工具层直接散落 HTTP 调用。
- 配置和密钥边界：API key 只来自环境变量或后续受控配置源，audit/log 不记录 key、完整 prompt、完整输出或完整 Evidence Pack。
- 超时和兜底：保留明确 timeout、provider error fallback、citation invalid fallback，让真实模型失败不破坏 `/chat` contract。
- 流式与结构化输出：后续若引入 streaming 或 patch proposal schema，应按 JavaGuide LLM API 工程实践参考处理取消、TTFT/总超时、断流、结构化解析失败和 fallback；结构化 patch/verification metadata 解析失败时不得直接 apply 或推进任务。
- 最小重试：如后续需要，只对网络瞬断、429/5xx 等可恢复错误做小次数、可测试的 deterministic retry；默认验证仍不得依赖真实网络。
- 幂等和审计：后续 patch apply、verification run 或 provider call 应有 request/attempt id，记录 provider、model、status、latency、retry count、parse failure 等摘要，避免重复确认导致重复 apply。
- 轻量路由：只在明确需求出现时支持按任务类型选择 provider/model，例如 grounded answer、rewrite、rerank 分开配置；不要提前做复杂策略引擎。
- 成本/用量摘要：可以先记录 provider、model、status、latency、token/cost 估算字段，但只进入内部 trace 或后续受控审计，不进入 `/chat.tool_calls`。

暂不追求完整工业 LLMGateway 能力：全局限流服务、熔断集群、复杂供应商竞价、多租户配额、持久化成本账单、分布式日志追踪或控制台。只有当 RepoPilot 真的开始依赖多个真实 provider、长任务 worker、connectors 或 always-on assistant 时，再作为独立阶段评估。

### Historical reference: Query Rewrite + Rerank (V12)

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

### Historical reference: Memory (V13)

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

### Historical reference: Long Task Control Plane + ReAct Skeleton (V14)

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

### Historical reference: Assistant Control Surface (V15)

V15 在 AgentLoop 前段加入只读助手控制面：

```text
AgentLoop
  -> MemoryManager(command)
  -> LongTaskManager(command)
  -> AssistantControlSurface(status summary)
  -> RequestRouter / capability-status / repo_search
```

边界约束：

- Assistant Control Surface 只通过现有 `/chat` 入口触发，不新增公开 API 或 `/chat` 顶层字段。
- 触发词包括 `助手状态`、`RepoPilot 状态`、`你能做什么`、`assistant status` 和 `what can you do`。
- 控制面只读聚合 Memory PREF/LTM/STM 计数和 Long Task 最近摘要；不存在本地 DB 时返回空状态，不创建 `.repopilot/`、`memory.sqlite3` 或 `tasks.sqlite3`。
- 控制面请求不调用 `repo_rag`，不进入 PermissionPolicy / ApprovalGate 工具调用链路，不写 memory，不创建或推进任务。
- 公开回答不得泄露完整 memory value、scratch、ReAct trace、完整 Evidence Pack、完整 provider output、本机绝对路径或 DB 路径。
- V15 不实现 patch proposal、diff apply、Verification Runner、Shell executor、SandboxRunner、后台任务、真实 subagent orchestration 或 worktree automation。

### Historical reference: Safe Patch Authoring (V16)

V16 在 AgentLoop 前段加入 Safe Patch Authoring：

```text
AgentLoop
  -> MemoryManager(command)
  -> LongTaskManager(command)
  -> AssistantControlSurface(status summary)
  -> PatchManager(proposal / confirm apply)
     -> proposal: ToolExecutor(repo_rag) -> EvidencePack -> PatchAuthoringProvider -> SQLitePatchStore
     -> apply: ToolInvocationContext -> PermissionPolicy -> ApprovalGate -> ToolExecutor(patch_apply)
```

边界约束：

- Patch proposal 只通过明确 patch 请求触发，并在 capability-status / repo_search 前处理。
- 默认 fake Patch Authoring provider 不生成真实 diff；`ModelPatchAuthoringProvider` 仅提供可注入
  实现边界，当前默认应用没有环境变量驱动的真实 patch provider 装配。注入模型时 Patch provider
  显式提供独立 JSON output instruction，query 只表达用户修改意图；任何输出仍必须通过业务字段、
  citation、路径和 diff 校验。
- Pending patch 存入 `.repopilot/patches.sqlite3`，按 `user_id + repo_key` 隔离，默认 24 小时过期。
- Apply 只接受 `确认 patch <patch_id>`、`应用 patch <patch_id>`、`confirm patch <patch_id>` 和 `apply patch <patch_id>`。
- `ToolInvocationContext` 由 Patch manager 预校验生成；`PermissionPolicy` 和 `ApprovalGate` 不读 patch store、不解析用户消息、不重新计算 hash。
- `PermissionPolicy` 仍只产出 `allow`、`deny` 或 `ask`；`patch_apply` 只有在有效确认上下文下走 `ask -> ApprovalGate pass`。
- `patch_apply` 是唯一写入路径，只修改 unified diff 中的 repo 内相对路径，并拒绝路径穿越、敏感文件、隐藏状态目录、二进制文件和 context mismatch。
- V16 不运行测试、不自动 commit、不创建 worktree、不执行 shell、不实现 Patch + Verify Loop。

### Historical reference: Verification Runner (V17)

V17 在 AgentLoop 前段加入受控 Verification Runner：

```text
AgentLoop
  -> MemoryManager(command)
  -> LongTaskManager(command)
  -> AssistantControlSurface(status summary)
  -> PatchManager(proposal / confirm apply)
  -> VerificationRunner(intent / whitelist)
     -> ToolInvocationContext
     -> PermissionPolicy -> ApprovalGate
     -> ToolExecutor(verification_run)
     -> subprocess runner(argv list, shell=False)
```

边界约束：

- Verification intent 在 Patch command / Patch intent 之后、capability-status / repo_search 之前处理。
- V17 只支持固定白名单标签：`pytest`、`ruff` 和 `verify`。三者都使用当前 `sys.executable`
  与 isolated mode：pytest 为 `-I -m pytest`，Ruff 为 `-I -m ruff check .`，`verify` 为
  `-I scripts/verify.py`；PowerShell 脚本只是同一 Python 入口的薄包装。
- V17 不支持用户附加参数、targeted pytest、`ruff --fix`、管道、重定向、环境变量赋值或任意 shell 文本。
- `verification_run` 注册为 `read_only=False`、`risk="write"`、`requires_approval=True`；只有有效 verification context 才能走 `ask -> ApprovalGate pass`。
- API handler、AgentLoop 和 parser 不直接调用 subprocess；实际执行只通过 `ToolExecutor.verification_run(...)`。
- runner 使用 argv list 和 `shell=False`，cwd 固定为 resolved `repo_path`。pytest/Ruff 在真正执行前
  通过 isolated child probe 检查模块可用性；缺失或 probe 异常明确 fail closed，不会静默跳过。
- pytest probe/执行删除继承的 `PYTEST_ADDOPTS` 与 `PYTEST_PLUGINS`，并固定
  `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`；解释器路径与 repo/local/secret 一起脱敏。
- stdout/stderr 各最多 4000 字符；`/chat.answer` 验证输出摘要总计最多 6000 字符，并标记 `truncated=true/false`。
- 公开响应脱敏 resolved repo path、本机绝对路径、`.repopilot/...` 和常见 secret，不公开完整 stdout/stderr、环境变量、完整 trace、Evidence Pack 或 provider prompt/output。
- V17 不自动串联 patch apply，不根据失败生成 patch，不持久化 verification result，不创建 worktree，不 commit/push。

### Historical reference: Patch + Verify Loop (V18)

V18 在 AgentLoop 前段加入明确组合确认闭环：

```text
AgentLoop
  -> MemoryManager(command)
  -> LongTaskManager(command)
  -> AssistantControlSurface(status summary)
  -> PatchManager(proposal / confirm apply / combined confirm)
  -> patch_apply
     -> ToolInvocationContext(patch_apply)
     -> PermissionPolicy -> ApprovalGate -> ToolExecutor(patch_apply)
  -> verification_run
     -> ToolInvocationContext(verification_run)
     -> PermissionPolicy -> ApprovalGate -> ToolExecutor(verification_run)
```

边界约束：

- 组合确认在 Patch command 分支内优先处理，优先级为 `组合确认 > 纯 verification intent > capability-status/repo_search`。
- 组合请求必须同时解析 `patch_id` 和 verification label；缺失 label、半解析、非法 label、附加参数或 shell 语法整体拒绝，不执行 `patch_apply`。
- 单独 patch 确认保持 apply-only 行为，不自动运行验证。
- apply 成功后才创建独立 verification context；不得复用 patch context。
- apply 失败、过期、hash mismatch、跨用户/跨 repo 或 scope invalid 时不运行验证。
- V18 不持久化 verification result、不生成后续 patch、不创建 worktree、不 commit/push、不调度 subagents。

</details>
