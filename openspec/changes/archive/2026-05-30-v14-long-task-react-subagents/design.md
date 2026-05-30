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
     -> LexicalRepoRetriever + EmbeddingRepoRetriever -> file_tools
```

V14 在 `AgentLoop` 内增加 Long Task 前置命令边界。Long Task 是 repo-local 本地状态能力，不是后台 worker、subagent runtime、worktree automation 或代码修改能力。

## Goals / Non-Goals

**Goals:**

- 支持明确 Long Task 聊天指令，并在路由前处理控制命令。
- 使用 `.repopilot/tasks.sqlite3` 持久化 user+repo 范围的任务、steps、scratch 和 ReAct trace 摘要。
- 创建任务时生成 deterministic task-type plan；显式配置 provider 时可辅助填充模板内字段，失败 fallback。
- 显式 resume/run 时一次推进一个 step，并只允许调用现有只读 `repo_rag`。
- 保持 `/chat` 顶层响应 contract 不变。

**Non-Goals:**

- 不新增 `/tasks` API 或 `/chat.task_summary`。
- 不执行后台任务、不自动循环执行、不执行 shell、不修改代码、不运行 SandboxRunner。
- 不创建、展示或调度真实 subagents。
- 不创建、切换或管理 git branch/worktree。
- 不实现 evaluator、reflection、自动语义验收或完整回滚。

## Decisions

### Decision 1: Long Task 指令优先于 RequestRouter

`AgentLoop` MUST 在调用 `RequestRouter.route(...)` 之前处理明确的前置控制命令：先解析 V13 Memory command，再解析 Long Task 控制命令。创建、查看、列出、暂停、补充、归档、reopen 等 Long Task 控制命令命中后 MUST 直接返回 Long Task answer，`related_files=[]`，`tool_calls=[]`，且 MUST NOT 调用 `repo_rag`。

显式 resume/run 是唯一可执行 step action 的 Long Task 命令；它仍 MUST 先完成任务状态校验，再通过 ToolRegistry、PermissionPolicy、ApprovalGate 和 ToolExecutor 调用 `repo_rag`。

### Decision 2: Repo-local tasks SQLite 与 V13 repo_key 规则

V14 使用 `Path(repo_path) / ".repopilot" / "tasks.sqlite3"`。任务 `repo_key` MUST 复用 V13 `compute_repo_key` / `normalize_repo_path_for_key` 规则：

1. `Path(repo_path).resolve()`。
2. 转换为 POSIX 分隔符字符串。
3. Windows 下 lower-case。
4. SHA-256 hash。

audit MUST NOT 暴露原始绝对路径或 DB 路径。

### Decision 3: 状态机和执行节奏

任务状态固定为 `pending`、`running`、`paused`、`blocked`、`completed`、`failed`，另有 `archived=true` 标记。创建任务后默认 `paused`，不自动执行。显式 resume/run 每次只推进当前 step。step 成功后，如果存在下一步，task 回到 `paused`；最后一步成功后 task 变为 `completed`。

`repo_rag` 成功但无结果时 task 进入 `blocked`，等待用户补充信息。工具失败时记录 attempt；同一 retry round 未满 3 次时 task 回到 `paused`，满 3 次后 task 变为 `failed`。`failed` MAY reopen for retry，并新增 retry round；`completed` MUST 只读不可变。

### Decision 4: Task type templates 是默认 planning

V14 默认按任务类型生成 deterministic templates。类型覆盖现有 `QueryUnderstanding` 五类：`code_location`、`implementation_explanation`、`call_relationship`、`test_or_validation`、`file_summary`，并新增 `stage_planning` 和 `unknown` fallback。每类固定 3-5 步，所有 step 的 `action_type` 固定为 `repo_rag`。

`stage_planning` 只在明确 Long Task 创建指令中包含阶段、OpenSpec、规划、V14 等词时触发，不改变普通 repo_search 的 QueryUnderstanding 行为。

### Decision 5: Provider planning 只能增强模板字段

显式配置真实 ModelProvider 后，V14 MAY 请求 provider 返回 JSON plan。provider 输出只能在既有模板 step 上填充 `title`、`query_hint`、`expected_outcome` 和 `acceptance_hint`，MUST NOT 改变 step 数、顺序或 action_type。JSON 解析、schema 校验或 provider 调用失败时，系统 MUST 使用 deterministic fallback plan 创建任务，并在 answer/audit 中记录 `plan_source=deterministic_fallback`。

### Decision 6: Scratch 和 ReAct trace 只保存摘要

scratch 保存用户目标、用户补充信息、step observation 摘要和 citation 引用。ReAct trace 保存 `thought_summary`、`action`、`observation_summary` 和 `status`。系统 MUST NOT 保存或公开完整 prompt、完整 Evidence Pack、完整 provider output、本机绝对路径或 DB 路径。

### Decision 7: Quota 和 archive

每个 `user_id + repo_key` 最多保留 20 个未归档任务。list 默认返回最近 10 个未归档任务。达到配额时，系统 MUST 拒绝创建新任务，并提示用户归档 completed/failed 任务。归档只设置 `archived=true`，不是物理删除；只能归档 completed/failed 任务。

## Error Behavior

- repo_path 不存在或 tasks DB 不可用：Long Task 命令返回脱敏失败回答，不执行 repo_search。
- 创建任务达到配额：拒绝创建，提示归档旧任务。
- 缺 task_id 且存在多个候选：返回候选列表，不改变任务状态。
- resume 已 completed 或 archived 任务：返回不可执行说明。
- provider planning 失败：fallback 到 deterministic plan。

## Rollback

V14 不修改 `/chat` 响应 schema。若 Long Task 出现问题，可禁用 AgentLoop 的 LongTaskManager 注入，回到 V13 行为；repo-local `.repopilot/tasks.sqlite3` 本地状态可由用户删除。
