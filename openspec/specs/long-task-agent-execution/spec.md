# long-task-agent-execution Specification

## Purpose
Define RepoPilot's repo-local Long Task control plane: explicit task commands, persisted task state, deterministic planning templates, one-step resume execution through read-only repo_rag, summary-level scratch/ReAct trace storage, quota/archive behavior, and non-goals for background workers, shell, worktrees, and real subagents.
## Requirements
### Requirement: 系统提供 repo-local Long Task 存储

系统 SHALL 提供 Long Task 存储能力，默认使用目标 repo 内 `.repopilot/tasks.sqlite3` 保存任务、steps、scratch 和 ReAct trace 摘要。Long Task 存储 MUST 使用 Python stdlib `sqlite3`，默认 MUST NOT 引入外部数据库、网络服务或新增运行时依赖。

Long Task repo_key MUST 复用 V13 `compute_repo_key` / `normalize_repo_path_for_key` 规则：`Path(repo_path).resolve()`、POSIX 分隔符、Windows lower-case 和 SHA-256 hash。audit MUST NOT 暴露原始绝对路径或 DB 路径。

#### Scenario: SQLite 初始化

- **WHEN** LongTaskStore 针对有效 repo_path 初始化
- **THEN** 系统在 `.repopilot/tasks.sqlite3` 中创建所需 schema
- **AND** 初始化不需要网络、API key 或外部服务

#### Scenario: repo_key 与 V13 Memory 一致

- **WHEN** 同一 repo_path 传给 Memory 和 Long Task 存储
- **THEN** 两者 MUST 使用同一规范化规则生成 repo_key
- **AND** audit summary 不包含原始绝对路径

### Requirement: Long Task 指令前置处理

系统 SHALL 在 `RequestRouter` / keyword 路由前解析明确 Long Task 指令。Long Task 与 V13 memory command 同级前置；若消息先匹配明确 memory command，系统 SHALL 按 memory command 处理，否则再尝试 Long Task 指令。创建、查看、列出、暂停、补充、归档和 reopen 指令命中后 MUST 返回 Long Task answer，MUST NOT 执行 repo_rag，且 `related_files` 和 `tool_calls` MUST 为空。显式 resume/run MAY 执行当前 step action，但该 action MUST 经过 ToolRegistry、PermissionPolicy、ApprovalGate 和 ToolExecutor。

#### Scenario: 创建任务不执行 repo_rag

- **WHEN** 用户发送 `创建长任务：分析 task_xxx 路由`
- **THEN** 系统创建 Long Task 并返回 task_id
- **AND** 系统 MUST NOT 先进入 repo_search route
- **AND** `tool_calls` 为空

#### Scenario: resume 通过权限边界执行一步

- **WHEN** 用户发送 `恢复任务 task_20260529_ab12`
- **THEN** 系统校验任务状态并准备当前 step
- **AND** 系统 MUST 在调用 repo_rag 前经过 PermissionPolicy 和 ApprovalGate
- **AND** 每次 resume 最多推进一个 step

### Requirement: Long Task 状态机稳定且可恢复

系统 SHALL 使用固定任务状态：`pending`、`running`、`paused`、`blocked`、`completed`、`failed`。系统 MUST 使用 `archived=true` 表示归档，而不是把 archived 作为执行状态。创建任务后默认 SHALL 为 `paused`，并且 MUST NOT 自动执行 step。

step 成功后，如果仍有后续 step，任务 MUST 回到 `paused`；最后一个 step 成功后任务 MUST 变为 `completed`。`repo_rag` 成功但无结果时任务 MUST 变为 `blocked`。工具失败未达到当前 retry round 最大尝试次数时任务 MUST 回到 `paused`；达到 3 次后任务 MUST 变为 `failed`。

#### Scenario: 成功推进一步后暂停

- **WHEN** 当前 step 成功获得 repo_rag 结果且仍有后续 step
- **THEN** 当前 step 标记 completed
- **AND** 任务状态变为 `paused`

#### Scenario: 最后一步完成任务

- **WHEN** 当前 step 是最后一步且成功完成
- **THEN** 任务状态变为 `completed`

#### Scenario: 无结果进入 blocked

- **WHEN** repo_rag 调用成功但没有检索结果
- **THEN** 当前 step 不标记 completed
- **AND** 任务状态变为 `blocked`

### Requirement: Long Task 支持补充、reopen、archive 和 quota

系统 SHALL 允许用户对任何非终态、未归档任务补充信息。对 `blocked` 任务补充信息后，系统 MUST 将任务转回 `paused`。`completed` 任务 MUST 只读不可变。`failed` 任务 MAY reopen for retry，且系统 MUST 保留历史失败记录并新增 retry round。

每个 `user_id + repo_key` 未归档任务数 MUST 限制为 20。list 默认 MUST 返回最近 10 个未归档任务。达到配额时系统 MUST 拒绝创建新任务，并提示用户归档 completed/failed 任务。系统 MUST 只允许归档 completed/failed 任务；归档 MUST NOT 物理删除任务。

#### Scenario: blocked 任务补充后恢复 paused

- **WHEN** 用户对 blocked 任务补充信息
- **THEN** 系统记录 scratch 摘要
- **AND** 任务状态变为 `paused`

#### Scenario: failed 任务 reopen 新增 retry round

- **WHEN** 用户 reopen failed 任务
- **THEN** 系统保留历史 failure trace
- **AND** 当前 step 进入新的 retry round
- **AND** 任务状态变为 `paused`

#### Scenario: quota 满时拒绝创建

- **WHEN** user+repo 已有 20 个未归档任务
- **THEN** 创建新任务 MUST 被拒绝
- **AND** 回答提示用户归档 completed/failed 任务

### Requirement: Long Task plan 使用模板和受控 provider 增强

系统 SHALL 默认使用 deterministic task-type templates 生成 3-5 个 step。模板 MUST 覆盖
`code_location`、`implementation_explanation`、`call_relationship`、`test_or_validation`、
`file_summary`、`stage_planning` 和 `unknown`。所有 V14 step 的 `action_type` MUST 为
`repo_rag`。

显式配置真实 ModelProvider 时，系统 MAY 请求 provider 返回 JSON plan 增强模板字段。Planner MUST
使用 `json_object` output mode，并显式提供只包含 Planner JSON shape 的 structured output
instruction。Planner query MUST NOT 重复拼接 JSON 格式指令。Provider MUST NOT 改变 step 数、
顺序或 `action_type`。

Planner MUST 在解析 provider content 前显式确认 provider status 为 success。provider status
非 success、非法 JSON、非 object JSON 或业务 schema 校验失败时，系统 MUST 使用 deterministic
fallback plan 并记录 `plan_source=deterministic_fallback`。

#### Scenario: stage_planning 只在明确长任务指令中触发

- **WHEN** 用户发送包含阶段、OpenSpec 或规划词的创建长任务指令
- **THEN** planner MAY 选择 `stage_planning` 模板
- **AND** 普通 repo_search 的 QueryUnderstanding 行为不因此改变

#### Scenario: Planner 显式描述 JSON 输出

- **WHEN** provider-assisted planning 被启用
- **THEN** Planner MUST 使用自己的 structured output instruction
- **AND** query content MUST 只包含任务上下文和模板步骤，不重复 JSON shape 指令

#### Scenario: provider status 非成功时直接 fallback

- **WHEN** provider response status 不是 success
- **THEN** Planner MUST 使用 deterministic fallback plan
- **AND** Planner MUST NOT 尝试解析 provider content

#### Scenario: provider 输出非法时 fallback

- **WHEN** provider planning 返回非法 JSON、非 object JSON 或非法 step schema
- **THEN** 系统使用 deterministic template 创建任务
- **AND** 回答或内部 audit 标记 fallback plan source

### Requirement: Scratch 和 ReAct trace 脱敏

系统 SHALL 保存摘要级 scratch 和 ReAct trace。scratch MAY 保存用户目标、用户补充信息、step observation 摘要和 citation 引用。ReAct trace MAY 保存 `thought_summary`、`action`、`observation_summary` 和 `status`。系统 MUST NOT 保存或公开完整 prompt、完整 Evidence Pack、完整 provider output、API key、本机绝对路径或 DB 路径。

#### Scenario: Long Task 公开响应不泄露内部状态

- **WHEN** `/chat` 返回 Long Task 创建、查看、恢复或补充结果
- **THEN** answer MAY 包含 task_id、status、title、当前或下一步标题、简短摘要和下一条建议命令
- **AND** answer MUST NOT 包含完整 scratch、完整 ReAct trace、完整 provider output、本机绝对路径或 DB 路径

### Requirement: Subagent 和 worktree 仅作为未来 metadata

V14 MAY 在内部模型中预留 subagent handoff metadata 和 worktree handoff intent。系统 MUST NOT 创建、展示、调度或执行真实 subagents。系统 MUST NOT 创建、切换或管理 git branch/worktree。

#### Scenario: V14 不执行 worktree 操作

- **WHEN** Long Task 创建或查看 handoff metadata
- **THEN** 系统 MAY 返回手工 handoff 摘要
- **AND** 系统 MUST NOT 执行 git branch、git switch 或 git worktree 操作

### Requirement: Long Task 提供只读控制面摘要

系统 SHALL 为 Assistant Control Surface 提供只读 Long Task 摘要。摘要 MAY 包含未归档任务数量，以及最近最多 3 个任务的 `task_id`、`status`、`title` 和当前或下一步标题。摘要 MUST NOT 包含完整 scratch、完整 ReAct trace、本机绝对路径或 DB 路径。

#### Scenario: 控制面读取 Long Task 摘要不创建 DB

- **WHEN** Assistant Control Surface 请求读取 Long Task 摘要，且 `.repopilot/tasks.sqlite3` 不存在
- **THEN** 系统返回未归档任务数量为 0 的摘要
- **AND** 系统 MUST NOT 创建 `.repopilot/` 目录或 `tasks.sqlite3`

### Requirement: Long Task Events Produce Persistent Audit Summaries

系统 SHALL record redacted persistent audit summaries for long task create, status, pause, resume, supplement, reopen, archive, and step-result events when an audit store is available.

Long task audit summaries MAY include task id, command/action, status, current step index/title, and observation summary. Long task audit summaries MUST NOT persist or expose full scratch, full ReAct trace, full Evidence Pack, provider prompt/output, DB path, local absolute path, API key, or secret.

#### Scenario: Long task resume audit summary is safe

- **WHEN** a long task resume/run command advances or attempts to advance one step
- **THEN** the persistent audit event records task id, action, status, and a redacted step summary
- **AND** it MUST NOT contain full provider output or full Evidence Pack content
