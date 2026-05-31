## Context

当前主链路是：

```text
API -> ChatService(trace_id) -> CodeAgent -> AgentLoop
  -> MemoryManager(STM/PREF/LTM command/read audit)
  -> LongTaskManager(command/status/step audit)
  -> QueryUnderstanding/SearchPlan -> QueryRewriteProvider
  -> ToolRegistry -> PermissionPolicy -> ApprovalGate
  -> ToolExecutor(repo_rag) -> HybridRepoRetriever -> Reranker -> EvidencePack/ContextBudget
     -> GroundedAnswerGenerator -> ModelProvider
```

V15 不新增 API，也不把控制面做成后台 worker。控制面是 `/chat` 内一个明确只读分支，用来回答“当前能做什么 / 状态如何 / 下一步怎么操作”。

## Goals / Non-Goals

**Goals:**

- 通过明确状态类消息触发 Assistant Control Surface。
- 聚合既有能力摘要、Memory 计数和 Long Task 未归档任务摘要。
- 保持 `/chat` 顶层响应字段不变。
- 控制面请求不调用 `repo_rag`，不写 memory，不创建 Long Task。
- 只读状态读取不隐式创建 `.repopilot/`、`memory.sqlite3` 或 `tasks.sqlite3`。

**Non-Goals:**

- 不新增 `/status`、`/tasks` 或其他 API。
- 不新增 `/chat.status`、`/chat.assistant_state` 或任何顶层字段。
- 不生成 patch、不 apply diff、不执行 shell、不运行验证命令。
- 不执行后台任务、不自动循环、不调度真实 subagents、不创建 worktree。
- 不把 OpenSpec、Superpowers、MCP、plugin 或外部 skill 写成 RepoPilot runtime 能力。

## Decisions

### Decision 1: 仅 `/chat` 作为控制面

V15 的公开入口继续是 `POST /chat`。控制面信息写入现有 `answer` 字段，`related_files=[]`，`tool_calls=[]`。这样避免在 V15 扩大 API surface，并保持 V16 patch proposal 和 V17 verification runner 的边界清晰。

### Decision 2: 前置顺序固定

AgentLoop 前置处理顺序为：

1. Memory command。
2. Long Task command。
3. Assistant Control Surface status。
4. capability-status。
5. repo_search / chat_only。

这样 `记住：...` 和 `创建长任务：...` 继续按既有控制命令处理；`memory 实现了吗?` 继续走 capability-status；只有明确助手状态请求进入 V15 控制面。

### Decision 3: 状态聚合只读且不初始化 DB

Memory summary 和 Long Task summary 使用只读路径：

- repo_path 不存在：返回 unavailable 摘要。
- `.repopilot/memory.sqlite3` 不存在：Memory PREF/LTM 计数为 0。
- `.repopilot/tasks.sqlite3` 不存在：Long Task 未归档任务数为 0。
- 读取失败：返回 unavailable 摘要，不泄露本机路径或 DB 路径。

V15 summary MUST NOT 调用现有会创建目录/DB 的 `for_repo(...)` 初始化路径。

### Decision 4: 控制面回答格式稳定但非结构化

控制面 answer 使用中文优先的简短文本，包含三段：

- 当前能力：代码仓库问答、Memory、Long Task、能力边界。
- 当前状态：PREF/LTM/STM 计数、未归档任务数量和最近最多 3 个任务。
- 下一步：建议用户可直接问代码问题、写 memory、创建/列出/恢复长任务。

公开回答 MUST NOT 包含完整 memory value、scratch、ReAct trace、Evidence Pack、provider output、本机绝对路径或 DB 路径。

## Error Behavior

- repo_path 缺失或不可访问：控制面返回状态不可用说明，但不进入 repo_search。
- Memory 或 Long Task summary 读取失败：该子系统标记 unavailable，其他状态继续返回。
- 控制面 formatter 不依赖真实 LLM、网络、API key 或外部数据库。

## Rollback

V15 不修改 `/chat` schema。若控制面行为需要回退，可移除 AgentLoop 中 Assistant Control Surface 分支；Memory、Long Task 和 repo RAG 主链路不受影响。
