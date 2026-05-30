# 当前 Review 清单

当前活跃阶段：暂无。

## V14 Archive Closeout Gate

- [x] V14 implementation commit 已创建：`ed48fa9 Add V14 long task control plane`。
- [x] V14 已 fast-forward 合并到 `main` 并推送到 `agentic-codeops/main`。
- [x] V14 change 已归档到 `openspec/changes/archive/2026-05-30-v14-long-task-react-subagents/`。
- [x] 长期 specs 已通过 `openspec archive v14-long-task-react-subagents -y` 同步。
- [x] `openspec list` 显示 no active changes。
- [x] V14 内部 self-review 和外部 review 均已处理，无已知 P0/P1/P2。
- [x] 下一阶段开始前必须先创建新 OpenSpec change，并同步 `.harness/allowed_files.md` 和 `.harness/review_checklist.md`。

## V14 Planning / Implementation Gate

- [x] V14 OpenSpec change 包含 proposal、design、tasks，以及 `long-task-agent-execution`、`agent-loop-tool-execution`、`chat-api` 和 `harness-development-workflow` spec delta。
- [x] Memory command 和 Long Task command 均优先于 `RequestRouter` / keyword 路由；前置顺序为 Memory command 先识别，然后 Long Task command。
- [x] 创建、查看、列出、暂停、补充、归档和 reopen 控制命令不得调用 `repo_rag`；`task_xxx` 不得误触发 repo_search。
- [x] 显式 resume/run 每次最多推进一个 step，且 step action 只能通过现有 `ToolExecutor(repo_rag)` 执行只读检索。
- [x] resume/run 调用 `repo_rag` 前必须保留 `ToolRegistry`、`PermissionPolicy` 和 `ApprovalGate` 边界。
- [x] `.repopilot/tasks.sqlite3` 使用独立 Long Task DB，不复用 V13 `memory.sqlite3`，不迁移为统一 state DB。
- [x] Long Task repo_key 复用 V13 `compute_repo_key` / `normalize_repo_path_for_key` 规则：resolve、POSIX 分隔符、Windows lower-case、SHA-256 hash。
- [x] task 状态机覆盖 `pending`、`running`、`paused`、`blocked`、`completed` 和 `failed`；`archived` 只能作为标记，不作为执行状态。
- [x] `completed` 任务只读不可变；`failed` 只能 reopen for retry，保留历史并新增 retry round，不做真正回滚。
- [x] 每个 `user_id + repo_key` 未归档任务配额为 20；list 默认返回最近 10 个未归档任务；archive 只允许 completed/failed 且不物理删除。
- [x] deterministic task-type templates 覆盖现有五类 QueryUnderstanding 类型、`stage_planning` 和 `unknown`；`stage_planning` 只在明确 Long Task 创建指令中触发。
- [x] provider-assisted planning 只能增强模板字段，不能改变 step 数、顺序或 `action_type`；provider 失败或 JSON 校验失败必须 fallback。
- [x] Scratch 和 ReAct trace 只保存摘要和 citation 引用，不保存或公开完整 prompt、完整 Evidence Pack、完整 provider output、本机绝对路径或 DB 路径。
- [x] `/chat` 顶层响应 contract 不新增必需字段；Long Task 公开信息只进入 `answer`，`tool_calls` 只保留实际 `repo_rag` 调用摘要。
- [x] V14 只预留 subagent/worktree metadata，不得创建、展示、调度真实 subagents，不得执行 git branch/worktree 操作。
- [x] 默认验证不依赖真实网络、API key、真实模型输出、外部队列或外部数据库。
- [x] V14 self-review 和外部 review 发现均已处理；当前无已知 P0/P1/P2。

## V13 Archive Closeout Gate

- [x] V13 implementation commit 已创建：`1b5696d Add V13 memory`。
- [x] V13 active change 已归档到 `openspec/changes/archive/2026-05-28-v13-memory/`。
- [x] 长期 specs 已在 archive 前同步。
- [x] `openspec list` 显示 no active changes。
- [x] `openspec validate --all` 通过。
- [x] `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1` 通过。
- [x] `git diff --check` 通过。
- [x] `powershell -ExecutionPolicy Bypass -File scripts/check_stage_docs.ps1` 通过。
- [x] `powershell -ExecutionPolicy Bypass -File scripts/check_stage_closeout.ps1` 通过。
- [x] `README.md`、`docs/PROGRESS.md`、`HANDOFF_TO_NEXT_CHAT.md`、`.harness/allowed_files.md` 和 `.harness/review_checklist.md` 不再把 V13 描述为 active。
- [x] 下一阶段只写成 planned / next，不写成 implemented。

## V13 Implementation Review

- [x] OpenSpec change 包含 proposal、design、tasks，以及 `memory`、`agent-loop-tool-execution` 和 `chat-api` spec delta。
- [x] `.repopilot/` 已加入 `.gitignore`，SQLite DB 只作为 repo-local 本地状态，不修改被分析仓库代码文件。
- [x] `repo_key` 使用 `Path(repo_path).resolve()`、POSIX 分隔符、Windows lower-case 和稳定 hash，audit 不暴露绝对路径。
- [x] Memory parser 先把全角冒号 `：` 归一化为半角 `:`，并覆盖中文/英文明确指令。
- [x] Memory command 命中后确认优先，不执行 `repo_rag`，`related_files=[]` 且 `tool_calls=[]`。
- [x] PREF/LTM 使用 SQLite 持久化，STM 使用进程内按 `user_id/session_id` 隔离。
- [x] STM 可通过 `stm:` / `会话:` 明确写入，并按 `user_id/session_id` 读取摘要。
- [x] PREF 可影响表达偏好，但代码事实仍由 repo evidence 和 citation validation 约束。
- [x] Memory audit 只进入内部 trace，不进入 `/chat` 顶层字段或 `tool_calls`。
- [x] repo_path 不存在、不可解析或 `.repopilot/` 不可写时 memory command 优雅失败且不泄露本机路径。
- [x] 普通 repo_search 的 memory read failure 不阻断检索，只记录 memory unavailable。
- [x] 默认验证不依赖真实网络、API key、外部数据库或真实模型输出。

## V11 Archive Closeout

- [x] V11 change 包含 proposal、design、tasks，以及 `grounded-answer-model-provider`、`agent-loop-tool-execution`、`chat-api` 和 `repo-query-understanding-rag` spec delta。
- [x] `httpx>=0.27.0` 已放入 `[project].dependencies`，作为可选 OpenAI-compatible provider 的运行时依赖。
- [x] 默认 provider 为 deterministic fake provider，真实 OpenAI-compatible provider 必须显式配置。
- [x] `/chat` 顶层响应 contract 不新增必需字段。
- [x] citation、fallback、provider audit 和脱敏边界已有测试覆盖。
- [x] `openspec validate --all` 通过。
- [x] `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1` 通过。
- [x] `git diff --check` 通过。
- [x] 内部 self-review 和外部 review 均已处理。
- [x] V11 active change 已归档到 `openspec/changes/archive/2026-05-26-v11-grounded-answer-model-provider-boundary/`。

## V12 Implementation Review

- [x] OpenSpec change 包含 proposal、design、tasks，以及 `repo-query-understanding-rag` / `agent-loop-tool-execution` spec delta。
- [x] deterministic rewrite 永远保留 `original` variant，额外 variants 最多 3 条，id 和模板顺序稳定。
- [x] rewrite 不改变 route、权限决策或整体 `question_type`。
- [x] rerank 只作用于 retrieval results 层，Evidence Pack budget/summary 和 grounded answer citation validation 语义不变。
- [x] 每个 rewrite variant 都执行 hybrid retrieval；不得因 original variant 为空跳过 rewrite-only variants。
- [x] 原始 query 的 path/symbol/exact token 直接命中在容量允许时不被 variant-only 结果挤掉。
- [x] symbol/path 查询保持 lexical anchor，embedding-only 弱命中不得绕过 grep-first baseline。
- [x] rewrite/rerank audit 只进入内部 trace，不进入 `/chat` 顶层字段或完整 `tool_calls`。
- [x] capability status 区分 deterministic rewrite/rerank 已实现和真实 LLM rewrite/rerank 未实现。
- [x] 默认验证不依赖真实网络、API key 或真实模型输出。

## V12 Archive Closeout Gate

- [x] 使用 `.harness/templates/stage_closeout.md` 更新 PROGRESS、HANDOFF 和 harness 状态。
- [x] V12 implementation commit 已创建：`aaddad2 Add V12 query rewrite rerank`。
- [x] V12 review follow-up commit 已创建：`4553b11 Fix V12 review follow-ups`。
- [x] V12 active change 已归档到 `openspec/changes/archive/2026-05-27-v12-query-rewrite-rerank/`。
- [x] 长期 specs 已在 archive 前同步。
- [x] `openspec list` 显示 no active changes。
- [x] `openspec validate --all` 通过。
- [x] `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1` 通过。
- [x] `git diff --check` 通过。
- [x] `powershell -ExecutionPolicy Bypass -File scripts/check_stage_docs.ps1` 通过。
- [x] `powershell -ExecutionPolicy Bypass -File scripts/check_stage_closeout.ps1` 通过。
- [x] `README.md`、`docs/PROGRESS.md`、`HANDOFF_TO_NEXT_CHAT.md`、`.harness/allowed_files.md` 和 `.harness/review_checklist.md` 不再把已归档阶段描述为 active。
- [x] 下一阶段只写成 planned / next，不写成 implemented。
