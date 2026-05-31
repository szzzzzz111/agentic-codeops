## Context

当前主链路是：

```text
API -> ChatService(trace_id) -> CodeAgent -> AgentLoop
  -> MemoryManager(STM/PREF/LTM command/read audit)
  -> LongTaskManager(command/status/step audit)
  -> AssistantControlSurface(read-only status)
  -> QueryUnderstanding/SearchPlan -> QueryRewriteProvider
  -> ToolRegistry -> PermissionPolicy -> ApprovalGate
  -> ToolExecutor(repo_rag) -> HybridRepoRetriever -> Reranker -> EvidencePack/ContextBudget
     -> GroundedAnswerGenerator -> ModelProvider
```

V16 在 Assistant Control Surface 之后插入 Patch command / Patch intent。Proposal 阶段仍先走 repo evidence；Apply 阶段只处理明确确认语法和 pending patch id。

## Goals / Non-Goals

**Goals:**

- 通过明确 patch 请求生成可审查 patch proposal。
- 将 pending patch 保存到 repo-local `.repopilot/patches.sqlite3`。
- 通过明确确认语法应用 pending patch。
- 写入只通过 `patch_apply`，并保留 `ToolRegistry -> PermissionPolicy -> ApprovalGate -> ToolExecutor` 边界。
- 保持 `/chat` 顶层响应字段不变。

**Non-Goals:**

- 不运行 `pytest`、`ruff` 或 `scripts/verify.ps1` 作为 runtime 行为。
- 不自动 commit、不创建 branch/worktree、不执行 shell。
- 不实现 Patch + Verify Loop、Persistent Audit / Recovery 或 Worktree Isolation。
- 不新增 `/patches`、`/status`、`/tasks` 或其他公开 API。
- 不把 OpenSpec、Superpowers、MCP、plugin 或外部 skill 写成 RepoPilot runtime 能力。

## Decisions

### Decision 1: Patch 前置顺序固定

AgentLoop 前置处理顺序为：

1. Memory command。
2. Long Task command。
3. Assistant Control Surface。
4. Patch command / Patch intent。
5. capability-status。
6. repo_search / chat_only。

这样 patch 请求不会被 repo_search 抢先处理；Memory、Long Task 和控制面仍保留既有优先级。

### Decision 2: 明确确认语法

Apply 只接受：

- `应用 patch <patch_id>`
- `确认 patch <patch_id>`
- `apply patch <patch_id>`
- `confirm patch <patch_id>`

不接受“可以”“继续”“就这样”等含糊表达。

### Decision 3: 结构化 Patch Authoring provider

Patch provider 输入只包含用户请求、问题类型、预算内 evidence snippets 和 citation metadata。输出必须是结构化 JSON，包含 `summary`、`target_files`、`diff` 和 `citations`。

默认 fake provider 返回不支持真实 diff 的安全 fallback，保证默认验证不依赖真实模型。OpenAI-compatible provider 只有在显式配置后才可生成 diff。

### Decision 4: Pending patch store 保存 diff

`.repopilot/patches.sqlite3` 保存 `patch_id`、`user_id`、`repo_key`、`status`、`target_files`、`diff_text`、`diff_hash`、`summary`、`created_at`、`updated_at` 和 `expires_at`。

pending patch 默认 24 小时过期。过期 patch 确认时标记 `expired`，不得 apply。

### Decision 5: ToolInvocationContext 只传归一化确认信息

Patch manager 在权限检查前读取 pending patch，校验 `user_id + repo_key`、状态、TTL、diff hash 和确认语法，然后构造 `ToolInvocationContext`。

`PermissionPolicy` 和 `ApprovalGate` 只消费 context，不直接读 DB、不解析用户消息、不重新计算 hash。

### Decision 6: 写入工具仍通过三态权限模型

`patch_apply` 注册为 `read_only=False`、`risk=write`、`requires_approval=True`。`PermissionPolicy` 仍只返回 `allow`、`deny` 或 `ask`。

当 `patch_apply` 的确认上下文全部有效时，`PermissionPolicy` 返回 `ask`，`ApprovalGate` 在同一 context 下判定通过。其他 `ask` 分支仍阻止执行。

### Decision 7: 全量 preflight 后写入

`patch_apply` 先解析 unified diff，对所有目标文件和 hunks 完成 preflight，并在内存中生成新内容。任一 preflight 失败时不写任何文件。

多文件写入阶段如果发生 I/O 失败，工具必须尝试恢复已写文件的原始内容，并把 patch 标记为 `failed`。成功后标记 `applied`。

## Error Behavior

- repo_path 不存在或不可用：patch proposal / apply 返回安全失败摘要，不泄露本机路径。
- provider error、JSON schema parse failure、非法 citation 或非法 diff：不创建 pending patch。
- pending patch 过期、状态非 pending、跨用户/跨 repo、hash 不匹配：拒绝 apply。
- context mismatch、敏感文件、二进制文件、路径穿越或 repo 外路径：拒绝 apply。

## Rollback

V16 不修改 `/chat` schema。若 patch authoring 需要回退，可移除 AgentLoop 中 Patch 分支和 `patch_apply` 工具规格；Memory、Long Task、Assistant Control Surface 和 repo RAG 主链路不受影响。
