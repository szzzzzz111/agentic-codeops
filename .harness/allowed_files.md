# 当前 Harness 写入边界

当前活跃阶段：V14 `v14-long-task-react-subagents`。

V14 目标是在现有 `/chat` 和 AgentLoop 边界内加入 Long Task Control Plane 与 ReAct trace skeleton。Long Task 指令必须先于 `RequestRouter` / keyword 路由前置处理；本阶段不新增 `/tasks` API、不新增 `/chat` 必需顶层字段、不执行后台任务、不创建 worktree、不调度真实 subagents、不执行 shell、不自动修改代码。

## 当前允许修改

- `README.md`
- `docs/ARCHITECTURE.md`
- `docs/PROGRESS.md`
- `docs/FEATURE_LIST.json`
- `HANDOFF_TO_NEXT_CHAT.md`
- `.gitignore`
- `.harness/allowed_files.md`
- `.harness/review_checklist.md`
- `.harness/templates/**`
- `scripts/check_stage_docs.ps1`
- `scripts/check_stage_closeout.ps1`
- `scripts/verify.ps1`
- `.harness/test_commands.md`
- `app/longtask/**`
- `app/harness/kernel.py`
- `app/agents/code_agent.py`
- `app/services/chat_service.py`
- `tests/test_long_task.py`
- `tests/test_agent_harness_kernel.py`
- `tests/test_chat_api.py`
- `openspec/changes/v14-long-task-react-subagents/**`
- `openspec/specs/**`
- `openspec/changes/archive/**`

## 禁止修改

- 不恢复旧 `specs/00x-*` 作为规格入口。
- 不把 OpenSpec、Superpowers、MCP、plugin 或参考项目写成 RepoPilot runtime 能力。
- 未创建并通过 review 新阶段 OpenSpec 前，不修改运行时代码或测试。
- 不新增 `/chat` 必需顶层字段。
- 不绕过 `ToolExecutor(repo_rag)`、`PermissionPolicy`、`ApprovalGate` 或安全文件工具边界。
- 不默认接入 Milvus、Elasticsearch、PgVector、Qdrant、真实外部 embedding 服务、模型下载、tokenizer 依赖或持久化向量索引。
- V12 已实现默认 deterministic query rewrite 和 deterministic rerank；V13 已实现 repo-local SQLite-backed Memory；后续不得把真实 LLM rewrite/rerank、向量 memory、自动 memory 总结、context compression、SandboxRunner、skill execution 或多 agent orchestration 写成已实现，除非新阶段明确开放。
- 不把小米 MiMo/Mino 写死为运行时主链路；真实 provider 只能作为 OpenAI-compatible provider 的显式配置。
- 不让默认验证依赖真实网络、真实 API key 或真实模型输出。
- Memory 只能写入 repo-local `.repopilot/` 本地状态目录；不得修改被分析仓库代码文件。
- Memory audit 不得暴露完整 memory value、本机绝对路径、DB 路径、完整 Evidence Pack 或模型输出。
- Long Task 控制命令不得先进入 `RequestRouter` / keyword 路由；创建、查看、列出、暂停、补充和归档不得调用 `repo_rag`。
- Long Task 只能在显式 `resume/run` 当前 step 时调用只读 `repo_rag`，且必须通过现有权限、审批和 `ToolExecutor` 边界。
- Long Task 状态写入只能进入 repo-local `.repopilot/tasks.sqlite3`；不得修改被分析仓库代码文件。
- Long Task audit、scratch 和 ReAct trace 不得暴露完整 prompt、完整 Evidence Pack、完整模型输出、本机绝对路径或 DB 路径。
- V14 只允许预留 subagent/worktree handoff metadata，不得创建、展示或调度真实 subagents，不得执行 git branch/worktree 操作。
