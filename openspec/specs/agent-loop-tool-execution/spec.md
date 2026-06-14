# agent-loop-tool-execution Specification

## Purpose

记录已实现的轻量 Agent Harness Kernel、确定性 Agent Loop、工具执行边界、V11 grounded answer 边界、V12 deterministic rewrite/rerank 边界和 V13 Memory 边界：`CodeAgent` 通过 `AgentLoop` 编排 `RequestRouter`、`MemoryManager`、`QueryUnderstanding`、`ToolRegistry`、`PermissionPolicy`、`ApprovalGate`、`ToolExecutor`、`GroundedAnswerGenerator` 和内存级 `TraceEvent`，从 repo-local hybrid RAG 结果生成 `related_files`、安全 `tool_calls` 摘要和基于证据的 `answer`。默认路径不依赖真实 LLM；显式配置后可通过 Model Provider Boundary 调用 OpenAI-compatible provider 生成 grounded answer。不修改代码、不执行 shell、不引入真实外部 embedding 服务、外部向量库、LLM query rewrite、LLM rerank、向量 Memory、自动 memory 总结、Reflection、eval、SandboxRunner 或复杂多 Agent。
## Requirements
### Requirement: Agent Loop 由轻量 Harness Kernel 编排

系统 SHALL provide a lightweight Agent Harness Kernel to orchestrate request routing, Memory boundaries, Long Task boundaries, Assistant Control Surface, Patch command / Patch intent, Verification intent, Persistent Audit / Recovery intent, tool metadata, tool calls, grounded answer boundaries, and trace events.

The fixed front-of-loop order SHALL be:

1. memory command
2. long task command
3. assistant control surface
4. patch command / patch intent
5. verification intent
6. audit recovery/status intent
7. capability/status intent
8. `RequestRouter` repo_search/chat_only fallback

Audit recovery/status intent MUST be handled after patch and verification intent so execution confirmations are not swallowed. Audit recovery/status intent MUST be handled before repo_search so recovery questions do not trigger repo RAG.

#### Scenario: Recovery intent does not call repo RAG

- **WHEN** the chat message is a recovery/status request such as recent audit records, recovery status, recent verification result, trace lookup, or patch lookup
- **THEN** AgentLoop MUST handle it before `RequestRouter`
- **AND** AgentLoop MUST NOT call `repo_rag`
- **AND** AgentLoop MUST NOT treat the request as capability-status unless the recovery parser does not match

#### Scenario: Patch and verification intents still outrank recovery

- **WHEN** the chat message is a patch confirmation, patch proposal, combined patch/verify confirmation, or explicit verification request
- **THEN** AgentLoop MUST handle that execution intent before checking recovery/status intent

### Requirement: 工具调用经过 ToolRegistry、PermissionPolicy、ApprovalGate 和 ToolExecutor

系统 SHALL 使用 `ToolRegistry` 记录工具规格元数据，并且 repo-local 检索、V16 patch apply 和 V17 verification run MUST 继续通过统一 `ToolExecutor` 边界执行。`ToolRegistry` MUST NOT 负责实际 dispatch。

`PermissionPolicy` MUST 继续只产出 `allow`、`deny` 或 `ask`。系统 SHALL 使用可选 `ToolInvocationContext`，使 `PermissionPolicy.decide(tool_spec, tool_name, context=None)` 和 `ApprovalGate.evaluate(decision, context=None)` 能消费已归一化的工具调用上下文。现有只读工具调用在未传 context 时 MUST 保持兼容。

`verification_run` MUST 注册为 `read_only=False`、`risk="write"`、`requires_approval=True` 的高风险工具。`verification_run` 只有在有效 verification context 下 MAY 由 `PermissionPolicy` 返回 `ask`，并由 `ApprovalGate` 判定通过。有效 context MUST 只携带归一化验证标签和 repo scope，不携带用户原始 shell 命令。非白名单命令、缺少有效 context、repo scope 无效或命令标签不匹配时 MUST 返回 `deny`。普通非 low 风险工具仍 MUST 按既有策略拒绝。

#### Scenario: verification_run 在有效上下文下通过审批

- **WHEN** `verification_run` 已注册且 `ToolInvocationContext` 表示白名单标签有效且 repo scope 有效
- **THEN** `PermissionPolicy` 返回 `ask`
- **AND** `ApprovalGate` 判定通过
- **AND** AgentLoop MAY 调用 `ToolExecutor.verification_run`

#### Scenario: verification_run 在无效上下文下被拒绝

- **WHEN** `verification_run` 缺少有效 verification context
- **THEN** `PermissionPolicy` 返回 `deny`
- **AND** AgentLoop MUST NOT 调用 `ToolExecutor.verification_run`

### Requirement: 聊天响应从真实搜索结果生成 related_files

系统 SHALL 从安全搜索结果填充 `related_files`，并在无命中时保持响应稳定。`related_files` MUST 只包含相对仓库路径；如果上游工具异常返回本机绝对路径，Kernel MUST 跳过该路径，避免通过 `/chat` 泄露。

#### Scenario: 搜索命中

- **WHEN** 安全仓库搜索找到匹配文件
- **THEN** `/chat` 在 `related_files` 中返回去重后的相对文件路径

#### Scenario: 搜索无命中

- **WHEN** 安全仓库搜索没有找到匹配文件
- **THEN** `/chat` 返回空 `related_files` 列表且响应仍成功

### Requirement: 工具调用摘要安全

系统 SHALL 返回包含工具名、参数摘要、状态和结果数量的工具调用摘要，并且 MUST NOT 泄露完整文件内容、完整搜索结果或本机绝对路径。

#### Scenario: repo-local hybrid RAG 调用摘要

- **WHEN** `/chat` 调用仓库搜索
- **THEN** `tool_calls` 包含 `repo_rag` 摘要、关键词、问题类型、检索模式、状态和结果数量
- **AND** 摘要不包含完整文件内容或本机绝对路径

### Requirement: Kernel 记录轻量 trace events

系统 SHALL 为 Kernel 执行过程记录结构化 trace events，至少包含路由和工具调用相关事件。当前 trace events 是内存级执行记录，不是持久化审计系统。Trace summary MUST 是脱敏摘要，MUST NOT 包含完整文件内容或本机绝对路径。

V7 的权限和审批审计事件仅记录在内部 `trace_events_internal`，MUST NOT 作为 `/chat` 顶层字段暴露。`AgentLoop` SHALL 负责记录 `permission_checked`、`tool_rejected` 和 `approval_required` 事件。`ApprovalGate` MUST NOT 自行记录 trace event。

#### Scenario: repo_search trace

- **WHEN** Kernel 执行仓库搜索
- **THEN** trace events 包含 `request_routed`
- **AND** trace events 包含 `permission_checked`
- **AND** trace events 包含 `tool_call`
- **AND** trace events 包含 `tool_result`

#### Scenario: chat_only 不进入权限链路

- **WHEN** Kernel 将请求路由为 `chat_only`
- **THEN** trace events 仅包含 `request_routed`
- **AND** trace events MUST NOT 包含 `permission_checked`
- **AND** `related_files` 为空列表
- **AND** `tool_calls` 为空列表

### Requirement: Agent Loop 不包含未来高风险能力

当前 Agent Loop MUST NOT 执行任意 shell 命令、执行 skill、使用真实外部 embedding 服务、使用外部向量库、执行 LLM query rewrite、执行 LLM rerank、执行向量 Memory、实现自动 LLM memory 总结、执行 Reflection、运行 eval、使用复杂多 Agent 编排或实现 SandboxRunner。

V17 SHALL 提供 Verification Runner。该能力 MAY 在明确验证请求和有效白名单上下文下运行 `pytest`、`ruff check .` 或 `scripts/verify.ps1`，但 MUST NOT 接受任意 shell、自动在 patch apply 后运行验证、根据验证失败自动生成 patch、持久化验证结果、commit、push、创建或管理 worktree、调度真实 subagents、执行后台任务或自动循环执行。

#### Scenario: V17 不执行 patch verify loop 或 git 操作

- **WHEN** 用户运行明确验证请求
- **THEN** 系统 MAY 执行白名单验证命令
- **AND** 系统 MUST NOT 自动生成 patch、commit、push 或创建 worktree

### Requirement: Kernel Records Persistent Audit Events

系统 SHALL attempt to record persistent audit summaries for each `/chat` trace envelope and for patch, verification, and long task events. Persistent audit recording MUST be best-effort and MUST NOT change the primary AgentLoop result if audit writing fails.

#### Scenario: Trace envelope is persisted for chat requests

- **WHEN** AgentLoop handles a `/chat` request
- **THEN** AgentLoop SHOULD record a lightweight trace envelope containing safe route/status/tool-count information
- **AND** the persisted envelope MUST NOT include full answer text, full trace, local absolute paths, or secrets

#### Scenario: Audit write failure preserves AgentLoop result

- **WHEN** persistent audit recording fails
- **THEN** AgentLoop returns the same public answer, related files, and tool call summaries as the primary path would return without audit persistence

### Requirement: Worktree Creation Uses The Existing Harness Boundary

系统 SHALL register a `worktree_create` execution tool for V20. `worktree_create` MUST pass through `ToolRegistry`, `PermissionPolicy`, `ApprovalGate`, and `ToolExecutor`, and MUST NOT be called directly from API handlers or free-form parsers.

Standalone patch apply and combined Patch + Verify MUST create a worktree first, then pass an internal `execution_repo_path` to `patch_apply` and combined `verification_run`. This execution path MUST NOT enter `/chat` top-level fields, `tool_calls`, or persistent audit payloads.

#### Scenario: Patch confirm uses isolated execution path

- **WHEN** a confirmed patch apply request passes worktree preconditions
- **THEN** AgentLoop first calls `worktree_create`
- **AND** `patch_apply` runs against the worktree execution repo path rather than the main repo path
### Requirement: Agent Loop Routes Worktree Inventory And Inspection As Strict Reads

系统 SHALL handle explicit worktree inventory and inspection intents before patch, verification, audit recovery, capability status, and repo-search fallback. These intents MUST NOT call repo RAG, verification, patch, cleanup, or any write tool.

Inspection SHALL emit `worktree_inspection` instead of the V20 `worktree_status` event. Inventory SHALL emit `worktree_inventory`.

#### Scenario: Worktree inspection replaces status event

- **WHEN** a user sends `worktree status <worktree_id>`
- **THEN** AgentLoop performs V21 inspection
- **AND** request-local trace contains `worktree_inspection`
- **AND** request-local trace does not contain `worktree_status`

### Requirement: Worktree Read Events Skip Persistent Audit

系统 SHALL preserve the unified `AgentLoop.run() -> _run_inner() -> _record_audit_and_return()` structure. `_skip_persistent_audit_for_result()` MUST skip persistent audit when a result contains `worktree_inventory` or `worktree_inspection`.

The request MAY retain safe in-memory trace events, but preview content MUST NOT enter those summaries.

#### Scenario: Existing audit database is unchanged

- **WHEN** inventory or inspection runs while an audit database already exists
- **THEN** the request returns its read-only answer
- **AND** no persistent audit row is added

### Requirement: Agent Loop Routes Worktree Re-verification Before Standalone Verification

系统 SHALL handle explicit retained worktree re-verification immediately after worktree inventory/inspection routing and before Patch + Verify, patch handling, standalone verification, audit recovery, capability status, and repo-search fallback.

The route MUST NOT call repo RAG, patch apply, cleanup, reconciliation, promotion, or any tool other than the approved existing `verification_run` after successful preflight.

#### Scenario: Re-verification is not swallowed by standalone verification

- **WHEN** a user sends `worktree verify <worktree_id> verify`
- **THEN** AgentLoop handles retained worktree re-verification
- **AND** it MUST NOT run standalone verification against the request repo path
