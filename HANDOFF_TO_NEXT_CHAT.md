# 交接给下一轮 Chat

## 当前状态

```text
当前基线分支：main
当前工作分支：codex/v15-assistant-control-surface
当前活跃 OpenSpec change：v15-assistant-control-surface
最近完成阶段：V14 Long Task Control Plane + ReAct Skeleton（已实现、review、提交、合并、推送并归档）
当前阶段：V15 Assistant Control Surface（implementation complete in current workspace）
```

RepoPilot 当前定位为面向代码仓库分析任务的可控 Code Agent Harness，不是替代通用 AI IDE 的编程助手。V1-V14 已归档；V15 已在当前工作分支加入只读 Assistant Control Surface，通过现有 `/chat.answer` 返回当前能力、Memory 计数、Long Task 摘要和下一步命令建议。默认不调用真实 LLM、网络或 API key。

后续路线已重排为 lightweight industrial harness：不是企业级平台，也不是玩具 demo；默认使用 SQLite、文件、进程内状态和白名单命令等轻量实现，但逐步交付可确认 patch、受控验证、失败恢复和隔离执行。该路线判断只是文档决策，不代表 V16+ 已启动，也不代表写代码、验证执行、worktree、subagents、connectors 或 always-on 已实现。

新增设计判断：RepoPilot adopts a grep-first, RAG-assisted retrieval stance。deterministic lexical/path/symbol search、exact match、文件树和路径线索是代码仓库分析的主要可审计检索基线；embedding/hybrid retrieval、query rewrite 和 rerank 只作为辅助召回或排序通道。V12 Query Rewrite / Rerank 服务于 grep-first baseline，不默认引入 Milvus、Elasticsearch、PgVector、Qdrant、重型 embedding cache 或真实 LLM rewrite/rerank。

V8 已归档到：

```text
openspec/changes/archive/2026-05-20-v8-query-understanding-repo-rag/
```

V9 已归档到：

```text
openspec/changes/archive/2026-05-22-v9-embedding-hybrid-search/
```

V11 已归档到：

```text
openspec/changes/archive/2026-05-26-v11-grounded-answer-model-provider-boundary/
```

V12 已归档到：

```text
openspec/changes/archive/2026-05-27-v12-query-rewrite-rerank/
```

V13 已归档到：

```text
openspec/changes/archive/2026-05-28-v13-memory/
```

V14 已归档到：

```text
openspec/changes/archive/2026-05-30-v14-long-task-react-subagents/
```

## 当前主链路

```text
API -> ChatService(trace_id) -> CodeAgent -> AgentLoop
  -> MemoryManager(STM/PREF/LTM command/read audit)
  -> LongTaskManager(command/status/step audit)
  -> AssistantControlSurface(read-only status)
  -> QueryUnderstanding/SearchPlan -> QueryRewriteProvider
  -> ToolRegistry -> PermissionPolicy -> ApprovalGate
  -> ToolExecutor(repo_rag) -> HybridRepoRetriever -> Reranker -> EvidencePack/ContextBudget
     -> GroundedAnswerGenerator -> ModelProvider
     -> LexicalRepoRetriever + EmbeddingRepoRetriever -> file_tools
```

`/chat` 顶层响应保持现有 contract：`trace_id`、`answer`、`related_files`、`tool_calls`。V7 的权限和审批审计、V8/V9 的 query understanding/retrieval 摘要、V10 的 Evidence Pack audit summary、V11 的 provider audit summary、V12 的 rewrite/rerank audit summary、V13 的 memory audit summary、V14 的 long task / ReAct 摘要和 V15 的 Assistant Control Surface 摘要只保留在内部 trace 或现有 `answer`，不作为 `/chat` 顶层字段暴露。

## V15 当前实现摘要

- OpenSpec change：`openspec/changes/v15-assistant-control-surface/`，包含 proposal、design、tasks，以及 `assistant-control-surface` / `agent-loop-tool-execution` / `chat-api` / `memory` / `long-task-agent-execution` / `harness-development-workflow` spec delta。
- `.harness/allowed_files.md` 和 `.harness/review_checklist.md` 已同步 V15 写入边界和 review gate。
- 新增 `app/assistant/control_surface.py`：明确触发词、只读状态聚合和 answer formatter。
- `AgentLoop` 前置顺序为 Memory command、Long Task command、Assistant Control Surface、capability-status、repo_search/chat_only。
- Memory / Long Task 增加只读 control surface summary；不存在 `.repopilot` DB 时返回空状态，不创建目录或 DB。
- V15 不新增 API，不新增 `/chat` 顶层字段，不调用 `repo_rag`，不写 memory，不创建任务，不执行 shell，不后台运行。
- 当前 targeted TDD 验证：`pytest tests/test_assistant_control_surface.py tests/test_agent_harness_kernel.py::test_agent_loop_answers_assistant_status_without_repo_rag tests/test_agent_harness_kernel.py::test_agent_loop_memory_command_still_precedes_assistant_status tests/test_agent_harness_kernel.py::test_agent_loop_long_task_command_still_precedes_assistant_status tests/test_chat_api.py::test_chat_endpoint_assistant_status_keeps_contract_and_does_not_create_state -q`：11 passed。
- OpenSpec / 默认验证记录：`openspec validate v15-assistant-control-surface` 通过；`openspec validate --all`：10 passed, 0 failed；`powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`：通过，`pytest` 144 passed, 1 skipped，`ruff check .` All checks passed，stage docs drift scan 无漂移；`git diff --check` 通过，仅有 CRLF 换行提示。
- V15 external review follow-up：已补测试并修复 Assistant Control Surface Long Task 摘要中 task title / next step title 的本机绝对路径脱敏；`pytest tests/test_assistant_control_surface.py::test_status_answer_redacts_absolute_paths_from_recent_long_tasks -q`：1 passed；V15 targeted 相关验证：11 passed；`openspec validate v15-assistant-control-surface` 通过；`openspec validate --all`：10 passed, 0 failed；`powershell -ExecutionPolicy Bypass -File scripts\verify.ps1`：通过，`pytest` 145 passed, 1 skipped，`ruff check .` All checks passed，stage docs drift scan 无漂移；`git diff --check` 通过，仅有 CRLF 换行提示；阶段文档已补齐 4.2-4.5 验证记录，`openspec/changes/v15-assistant-control-surface/tasks.md` 完成状态保留。
- V15 external review close：用户确认外部 review 没问题；final stage debt sweep 已执行，未发现新的 P0/P1/P2 或需记录的阶段内剩余债务。当前工作区尚未提交、尚未归档。

## V14 当前实现摘要

- OpenSpec change 已归档到 `openspec/changes/archive/2026-05-30-v14-long-task-react-subagents/`，包含 proposal、design、tasks 和 `long-task-agent-execution` / `agent-loop-tool-execution` / `chat-api` / `harness-development-workflow` spec delta。
- 长期 specs 已同步，新增 `openspec/specs/long-task-agent-execution/spec.md`。
- V14 archive 后 `.harness/allowed_files.md` 和 `.harness/review_checklist.md` 曾切回暂无 active stage；当前已由 V15 active change 重新同步为 V15 写入边界和 review gate。
- 新增 `app/longtask/`：
  - `parser.py`：解析明确长任务自然语言指令。
  - `planner.py`：deterministic task-type templates，并支持显式真实 provider 的受控 JSON 增强和 fallback。
  - `store.py`：repo-local `.repopilot/tasks.sqlite3`，复用 V13 repo_key 规范化规则。
  - `manager.py`：create/list/status/pause/resume/supplement/reopen/archive、quota 和状态流转。
- `AgentLoop` 已在 `RequestRouter` 前处理 Memory command 和 Long Task 指令，顺序为 Memory command 先识别、Long Task command 后识别；控制命令不调用 `repo_rag`，显式 resume/run 通过 `ToolRegistry -> PermissionPolicy -> ApprovalGate -> ToolExecutor(repo_rag)` 推进一个 step。
- Long Task 使用 `paused/running/blocked/completed/failed` 状态，`archived` 是标记；`completed` 只读，`failed` 可 reopen for retry。
- V14 不新增 `/tasks` API，不新增 `/chat` 必需顶层字段，不执行后台任务、不自动循环、不创建 worktree、不调度真实 subagents、不执行 shell、不自动修改代码。
- 当前验证：
  - `openspec validate v14-long-task-react-subagents`：通过。
  - TDD RED：`pytest tests\test_long_task.py tests\test_agent_harness_kernel.py::test_agent_loop_handles_long_task_command_before_router_keyword tests\test_chat_api.py::test_chat_endpoint_long_task_create_keeps_contract_and_does_not_search -q`：预期失败，缺少 `app.longtask`。
  - V14 目标验证：`pytest tests\test_long_task.py tests\test_agent_harness_kernel.py::test_agent_loop_handles_long_task_command_before_router_keyword tests\test_agent_harness_kernel.py::test_agent_loop_resumes_one_long_task_step_through_repo_rag tests\test_agent_harness_kernel.py::test_agent_loop_blocks_long_task_when_resume_has_no_results tests\test_chat_api.py::test_chat_endpoint_long_task_create_keeps_contract_and_does_not_search tests\test_chat_api.py::test_chat_endpoint_long_task_resume_returns_repo_rag_tool_call -q`：9 passed。
  - V14 相关集成：`pytest tests\test_long_task.py tests\test_agent_harness_kernel.py tests\test_chat_api.py -q`：60 passed。
  - V14 self-review follow-up：直接 `task_id` 访问补充 `user_id + repo_key` 隔离；新增测试先失败后修复。
  - V14 follow-up 相关验证：`pytest tests\test_long_task.py::test_manager_rejects_cross_user_task_id_access tests\test_long_task.py tests\test_agent_harness_kernel.py tests\test_chat_api.py -q`：62 passed。
  - V14 review follow-up RED：completion 阶段跨用户隔离与 provider JSON planning schema 测试先失败，分别暴露缺少 scoped completion 和 provider prompt 协议不足。
  - V14 review follow-up 修复：`complete_tool_action` 增加 `user_id + repo_key` 作用域校验；provider planning prompt 明确 JSON-only schema 和不可改变 step/action 边界。
  - V14 review follow-up targeted 验证：`pytest tests\test_long_task.py::test_planner_sends_json_schema_prompt_for_provider_enhancement tests\test_long_task.py::test_manager_rejects_cross_user_tool_completion -q`：2 passed。
  - V14 review follow-up 相关验证：`pytest tests\test_long_task.py tests\test_agent_harness_kernel.py tests\test_chat_api.py -q`：63 passed。
  - V14 review follow-up lint：`ruff check app\longtask app\harness\kernel.py tests\test_long_task.py tests\test_agent_harness_kernel.py tests\test_chat_api.py`：All checks passed。
  - V14 OpenSpec change 验证：`openspec validate v14-long-task-react-subagents`：通过。
  - V14 review follow-up 默认验证：`powershell -ExecutionPolicy Bypass -File scripts\verify.ps1`：通过；`pytest` 132 passed, 1 skipped；`ruff check .` All checks passed；stage docs drift scan 无漂移。
  - V14 review follow-up OpenSpec 全量验证：`openspec validate --all`：9 passed, 0 failed。
  - V14 external review triage：修复 Memory/Long Task 前置顺序、Long Task result summary 绝对路径脱敏，并清理 `app/longtask/__pycache__` 生成物；新增 targeted tests 先失败后修复。
  - V14 external review targeted 验证：`pytest tests\test_agent_harness_kernel.py::test_agent_loop_handles_memory_command_before_router_and_long_task tests\test_agent_harness_kernel.py::test_agent_loop_memory_command_confirms_without_repo_rag tests\test_long_task.py::test_manager_tool_completion_summary_redacts_absolute_paths -q`：3 passed。
  - V14 external review 相关验证：`pytest tests\test_long_task.py tests\test_agent_harness_kernel.py tests\test_chat_api.py -q`：65 passed。
  - V14 external review OpenSpec 验证：`openspec validate v14-long-task-react-subagents` 通过；`openspec validate --all`：9 passed, 0 failed。
  - V14 external review 默认验证：`powershell -ExecutionPolicy Bypass -File scripts\verify.ps1`：通过；`pytest` 134 passed, 1 skipped；`ruff check .` All checks passed；stage docs drift scan 无漂移。
  - V14 external review close：外部 review 确认无新增 P0/P1/P2；剩余 P3 `app/longtask/__pycache__` 已复核，文件系统和 git tracked files 均无 pyc。
  - Implementation commit：`ed48fa9 Add V14 long task control plane`。
  - Merge/push：已 fast-forward 合并到 `main` 并推送到 `agentic-codeops/main`。
  - Archive：`openspec archive v14-long-task-react-subagents -y` 已完成，长期 specs 已同步。
  - Archive 后 `openspec validate --all`：9 passed, 0 failed。
  - Archive 后默认验证：`powershell -ExecutionPolicy Bypass -File scripts\verify.ps1`：通过；`pytest` 134 passed, 1 skipped；`ruff check .` All checks passed；stage docs drift scan 无漂移。
  - Archive closeout：`powershell -ExecutionPolicy Bypass -File scripts\check_stage_closeout.ps1`：通过；包含 no active changes、OpenSpec 全量验证、stage docs drift scan 和 `git diff --check`。
  - `ruff check app\longtask app\harness\kernel.py tests\test_long_task.py tests\test_agent_harness_kernel.py tests\test_chat_api.py`：All checks passed。
  - `powershell -ExecutionPolicy Bypass -File scripts\verify.ps1`：通过；`pytest` 130 passed, 1 skipped；`ruff check .` All checks passed；stage docs drift scan 无漂移。
  - `git diff --check`：通过，仅有 CRLF 换行提示。

## V13 实现摘要

- 新增 `app/memory/store.py`，提供 `SQLiteMemoryStore`、`InMemorySessionMemoryStore`、`compute_repo_key` 和 repo path normalization。
- 新增 `app/memory/manager.py`，提供明确 memory 指令解析、记住/忘记、普通请求 memory summary 和脱敏 audit。
- `ChatService -> CodeAgent -> AgentLoopRequest` 已传入 `user_id` 和 `session_id`。
- V14 external review follow-up 后，`AgentLoop` 在 route 前处理 memory command；命中后返回确认，不执行 `repo_rag`。
- 普通 repo_search 在权限通过后记录 `memory_summarized`，memory read failure 不阻断检索。
- `.gitignore` 已加入 `.repopilot/`，repo-local SQLite DB 被视为本地状态。
- Implementation commit：`1b5696d Add V13 memory`。
- Archive：`openspec archive v13-memory --skip-specs -y` 已完成；长期 specs 已在 archive 前同步。
- 当前验证：
  - `openspec validate v13-memory`：通过。
  - `pytest tests\test_memory.py -q`：5 passed。
  - `pytest tests\test_memory.py tests\test_agent_harness_kernel.py tests\test_chat_api.py -q`：57 passed。
  - `openspec validate --all`：9 passed, 0 failed。
  - `powershell -ExecutionPolicy Bypass -File scripts\verify.ps1`：通过；`pytest` 120 passed, 1 skipped；`ruff check .` All checks passed；stage docs drift scan 无漂移。
  - `git diff --check`：通过，仅有 CRLF 换行提示。
  - Archive 后 `openspec list`：No active changes found。
  - Archive 后 `openspec validate --all`：8 passed, 0 failed。
  - Archive closeout：`powershell -ExecutionPolicy Bypass -File scripts/check_stage_closeout.ps1`：通过。
  - Archive 后默认验证：`powershell -ExecutionPolicy Bypass -File scripts\verify.ps1`：通过；`pytest` 120 passed, 1 skipped；`ruff check .` All checks passed；stage docs drift scan 无漂移。

## V12 实现摘要

- 新增 `app/rag/query_rewrite.py`，提供 `QueryRewriteProvider` 边界、`QueryRewriteResult`、`QueryVariant` 和默认 deterministic Code Evidence variants。
- 新增 `app/rag/rerank.py`，提供 before-Evidence deterministic rerank 边界和 fallback。
- `ToolExecutor.search_repo_rag` 对 rewrite variants 执行 bounded multi-query retrieval，合并去重后 rerank，再构建 Evidence Pack；original variant 为空时不跳过 rewrite-only variants。
- `HybridRepoRetriever` 对包含 `symbols` 或 `path_hints` 的查询保持 lexical anchor，避免 rewrite 模板词产生 embedding-only 误召回。
- `AgentLoop` 记录 `query_rewrite_summarized` 和 `rerank_summarized` 内部 trace；`/chat.tool_calls` 不暴露完整 variants、完整 retrieval results 或完整 Evidence Pack。
- V12 保持 Evidence Pack budget/summary 和 grounded answer citation validation 语义不变。
- Implementation commit：`aaddad2 Add V12 query rewrite rerank`。
- Review follow-up commit：`4553b11 Fix V12 review follow-ups`。
- Archive：`openspec archive v12-query-rewrite-rerank --skip-specs -y` 已完成；长期 specs 已在 archive 前同步。
- 当前验证：
  - `openspec validate v12-query-rewrite-rerank`：通过。
  - `pytest tests\test_query_rewrite.py tests\test_repo_rerank.py tests\test_agent_harness_kernel.py -q`：41 passed。
  - `pytest tests\test_query_rewrite.py tests\test_repo_rerank.py tests\test_repo_rag.py tests\test_agent_harness_kernel.py tests\test_chat_api.py tests\test_evidence_pack.py tests\test_grounded_answer.py -q`：72 passed。
  - `openspec validate --all`：8 passed, 0 failed。
  - `powershell -ExecutionPolicy Bypass -File scripts\verify.ps1`：通过；`pytest` 104 passed, 1 skipped；`ruff check .` All checks passed；stage docs drift scan 无漂移。
  - `git diff --check`：通过，仅有 CRLF 换行提示。
- V12 外部 review follow-up：
  - 已修正 original variant 为空时跳过 rewrite-only variants 的召回问题。
  - 已将 variant 去重改为按 `query_text`、`keywords`、`symbols`、`path_hints` 分字段归一化。
  - 已为 symbol/path 查询加入 lexical anchor，避免 rewrite 模板词产生 embedding-only 误召回。
  - `pytest tests/test_chat_api.py::test_chat_endpoint_returns_empty_related_files_when_keyword_is_missing tests/test_repo_rag.py tests/test_query_rewrite.py tests/test_tool_executor.py tests/test_repo_rerank.py -q`：19 passed。
  - `openspec validate v12-query-rewrite-rerank`：通过。
  - `openspec validate --all`：8 passed, 0 failed。
  - `powershell -ExecutionPolicy Bypass -File scripts\verify.ps1`：通过；`pytest` 108 passed, 1 skipped；`ruff check .` All checks passed；stage docs drift scan 无漂移。
- V12 archive closeout：
  - `openspec list`：No active changes found。
  - `openspec validate --all`：7 passed, 0 failed。
  - `powershell -ExecutionPolicy Bypass -File scripts/check_stage_closeout.ps1`：通过。
  - `powershell -ExecutionPolicy Bypass -File scripts\verify.ps1`：通过；`pytest` 108 passed, 1 skipped；`ruff check .` All checks passed；stage docs drift scan 无漂移。
  - `git diff --check`：通过，仅有 CRLF 换行提示。

## V11 实现摘要

- 新增 `app/providers/model_provider.py`，提供 `ModelProvider` 边界、deterministic `FakeModelProvider`、`OpenAICompatibleModelProvider` 和环境变量 provider factory。
- 新增 `app/answering/grounded_answer.py`，提供 grounded answer、citation validation、fallback 和 provider audit 汇总。
- `AgentLoop` 在 successful `repo_rag` 且存在 Evidence Pack 后调用 `GroundedAnswerGenerator`；工具错误仍沿用原有失败回答。
- citation 格式为 `relative/path.py:start-end`；无合法 citation、越界 citation、provider error、timeout 或 invalid response 均降级为保守 fallback。
- 默认 provider 为 fake，默认验证不需要网络、API key 或真实模型输出。
- OpenAI-compatible provider 使用运行时依赖 `httpx`，通过 `REPOPILOT_MODEL_PROVIDER=openai_compatible`、`REPOPILOT_MODEL_BASE_URL`、`REPOPILOT_MODEL_API_KEY`、`REPOPILOT_MODEL_NAME` 显式启用。
- provider audit 不进入 `/chat` 顶层字段或 `tool_calls`，且不记录完整 prompt、完整模型输出、完整 Evidence Pack 或 API key。
- V11 仍不实现 query rewrite、rerank、memory、context compression、SandboxRunner、skill execution 或多 agent orchestration。
- 当前验证：
  - `openspec validate v11-grounded-answer-model-provider-boundary`：通过。
  - `pytest tests\test_model_provider.py tests\test_grounded_answer.py tests\test_agent_harness_kernel.py tests\test_chat_api.py`：54 passed。
  - `openspec validate --all`：8 passed, 0 failed。
  - `powershell -ExecutionPolicy Bypass -File scripts\verify.ps1`：通过；`pytest` 97 passed, 1 skipped；`ruff check .` All checks passed。
  - `git diff --check`：通过，仅有 CRLF 换行提示。
- Archive：`openspec archive v11-grounded-answer-model-provider-boundary --skip-specs -y` 已完成；长期 specs 已在 archive 前同步。
- Archive 后验证：`openspec validate --all`：7 passed, 0 failed；`powershell -ExecutionPolicy Bypass -File scripts\verify.ps1`：通过；`pytest` 97 passed, 1 skipped；`ruff check .` All checks passed；`git diff --check`：通过，仅有 CRLF 换行提示。
- 外部 review follow-up：
  - 已确认 `httpx>=0.27.0` 位于 `[project].dependencies`，并在 PROGRESS 中补充运行时依赖变更记录。
  - 已修正 citation 校验 allowed 集合，使其只接受实际传给 provider 的 included 且非空 snippet evidence。
  - `pytest tests\test_grounded_answer.py`：9 passed。

## LLMGateway 设计备忘

用户补充的 LLMGateway 概念应作为后续真实模型调用增强参考，但不要写成当前 runtime 已实现能力。当前项目只有 V11 Model Provider Boundary：统一 provider 接口、fake/openai-compatible provider、环境变量配置、基础 timeout、provider error fallback、citation validation 和脱敏 audit。

后续对 RepoPilot 有价值的轻量方向：

- 继续把真实模型调用收口在 `ModelProvider` / `GroundedAnswerGenerator`，避免散落 HTTP 调用。
- 保持 API key、prompt、模型输出、Evidence Pack 的脱敏边界。
- 在需要时加入小次数 retry、latency/token/cost 摘要和简单 provider/model routing。
- JavaGuide LLM API 工程实践（`https://javaguide.cn/ai/llm-basis/llm-api-engineering.html`）可作为 V15-V17 规划参考：重点吸收流式输出取消/超时、结构化返回 schema/fallback、request/attempt id、重试幂等、解析失败率和 provider audit 摘要；不要照搬企业级网关。
- 不提前实现工业级限流、熔断集群、多租户成本账单、供应商竞价或控制台。

这个备忘适合后续 V15 或单独 `llm-gateway-lite` change 规划时参考。

## 已完成阶段摘要

### V7：Permission + Approval Gate

- 已提交：`7f1fc86 Add V7 permission approval gate`
- 已合并到 `main`：`Merge V7 permission approval gate`
- 已归档到：`openspec/changes/archive/2026-05-19-v7-permission-approval-gate/`
- 已实现 `ToolSpec.requires_approval`、`PermissionDecision`、`PermissionPolicy` 和最小 `ApprovalGate`。
- 权限优先级：未注册、非只读或非 `low` 风险 -> `deny`；否则 `requires_approval=True` -> `ask`；否则 -> `allow`。
- `deny` 和 `ask` 分支不调用 executor，`related_files=[]` 且 `tool_calls=[]`。

### V8：Query Understanding + Lexical Repo RAG

- 已提交：`2ab1316 Add V8 query understanding repo RAG`
- 已合并到 `main`：`cef8115 Merge V8 query understanding repo RAG`
- 已归档：`eff51c3 Archive V8 query understanding repo RAG`
- 已新增 deterministic `QueryUnderstanding/SearchPlan`。
- 已新增 repo-local lexical RAG：repo chunk、lexical scoring、dedup 和 citation。
- 已将 `/chat` 的 repo_search 分支从简单 `search_code` 搜索升级为 V8 的 `ToolExecutor(repo_rag) -> LexicalRepoRetriever`；后续 V9 已进一步升级为 `HybridRepoRetriever`，当前 V10 在此基础上加入 Evidence Pack / Context Budget。
- 已同步长期 specs：
  - `openspec/specs/agent-loop-tool-execution/spec.md`
  - `openspec/specs/repo-query-understanding-rag/spec.md`

V8 不实现 embedding、Milvus、Elasticsearch、PgVector、Qdrant、LLM rewrite、rerank、memory、SandboxRunner、skill execution 或多 agent orchestration。

### V9：Embedding Retrieval + Hybrid Search

- 已提交：
  - `61a7963 Add V9 embedding hybrid search`
  - `24d4d6e Fix V9 review follow-ups`
  - `d31e83e Document V9 implementation review recovery`
  - `9479a0c Address final V9 review findings`
  - `e5e5fa0 Archive V9 embedding hybrid search`
- 已归档到：`openspec/changes/archive/2026-05-22-v9-embedding-hybrid-search/`
- 已实现 `DeterministicEmbeddingProvider`、`EmbeddingRepoRetriever`、`HybridRepoRetriever` 和 deterministic `hybrid_fuse`。
- 默认 embedding provider 是本地确定性实现，不调用网络、密钥、模型下载或外部服务。
- `ToolExecutor(repo_rag)` 和 `AgentLoop` 默认使用 `retrieval_mode=hybrid`，同时保留 lexical retrieval 作为一等通道。
- 内部 trace 记录 hybrid channel audit summary，包括 lexical、embedding、fused 结果数和 `min_fused_score`；该摘要不作为 `/chat` 顶层字段暴露。
- V9 不默认引入 Milvus、Elasticsearch、PgVector、Qdrant、真实外部 embedding 服务、模型下载、LLM rewrite、rerank、memory 或 context compression。

## 当前 Harness 状态

- 当前 active change：`openspec/changes/v15-assistant-control-surface/`。
- `.harness/allowed_files.md` 已同步为 V15 写入边界。
- `.harness/review_checklist.md` 已同步 V15 planning / implementation gate，并保留 V14 及更早历史 review/closeout 记录。
- V15 当前允许修改范围集中在 `app/assistant/**`、`app/harness/kernel.py`、Memory/Long Task 只读 summary、相关测试、OpenSpec 和阶段文档。
- V15 当前禁止新增 API、新增 `/chat` 顶层字段、调用 `repo_rag`、写 memory、创建任务、执行 shell、生成 patch、运行验证 runner、创建 worktree 或调度真实 subagents。
- V1-V14 active changes 均已归档；历史实现摘要保留在本 handoff 后续章节，仅作为阶段背景，不代表当前 active change。

## V10 实现摘要

- 新增 `app/rag/evidence.py`，提供内部 Evidence Pack、Evidence item 和 Context Budget。
- `ToolExecutor.search_repo_rag` 在 successful hybrid retrieval 后生成 `ToolExecutionResult.evidence_pack`；工具错误时不伪造 Evidence Pack。
- Evidence item 固定包含 `evidence_id`、`file_path`、`start_line`、`end_line`、`score`、`snippet`、`source_summary`、`included` 和 `truncated`。
- Context Budget 默认 `max_context_chars=4000`，按 retrieval 顺序纳入 evidence，必要时裁剪最后一条。
- 内部 audit summary 固定包含 `evidence_items`、`included_count`、`omitted_count`、`truncated_count`、`budget_used_chars` 和 `max_context_chars`。
- `evidence_pack` 不进入 `call_summary()`、`/chat.tool_calls` 或 `/chat` 顶层响应。
- V10 仍不实现 grounded answer、model provider、prompt assembly、query rewrite、rerank、memory 或 context compression。
- V10 最新验证：
  - `openspec validate v10-evidence-pack-context-budget`：通过。
  - `pytest tests\test_evidence_pack.py tests\test_agent_harness_kernel.py tests\test_chat_api.py`：40 passed。
  - `powershell -ExecutionPolicy Bypass -File scripts\verify.ps1`：通过；`pytest` 75 passed, 1 skipped；`ruff check .` All checks passed。
  - `git diff --check`：通过，仅有 CRLF 换行提示。
- V10 review 收口：
  - 内部 self-review 未发现 P0/P1 阻塞；发现的 P2 历史文档措辞债已修正。
  - 外部 review：用户反馈外部 review 显示没问题，无阻塞发现。
  - 外部 review 后 full verify：`powershell -ExecutionPolicy Bypass -File scripts\verify.ps1` 通过；`pytest` 81 passed, 1 skipped；`ruff check .` All checks passed。
  - 实现提交：`c5ec1ff Add V10 evidence pack context budget`。
  - Archive：已移动到 `openspec/changes/archive/2026-05-26-v10-evidence-pack-context-budget/`，并同步长期 `repo-query-understanding-rag` spec。
  - Archive 后验证：`openspec validate --all` 6 passed, 0 failed；`powershell -ExecutionPolicy Bypass -File scripts\verify.ps1` 通过，`pytest` 81 passed, 1 skipped，`ruff check .` All checks passed；`git diff --check` 通过，仅有 CRLF 提示。
- V10 review follow-up：
  - 已修正长期 `agent-loop-tool-execution` spec，允许 repo-local deterministic hybrid RAG，不再禁止 V9 的本地 deterministic embedding retrieval。
  - 已把 `docs/FEATURE_LIST.json` 的 V8 条目标注为历史 lexical 验收口径，并指向当前 V9/V10 hybrid 口径。
  - `openspec validate --all`：7 passed, 0 failed。
  - `powershell -ExecutionPolicy Bypass -File scripts\verify.ps1`：通过；`pytest` 76 passed, 1 skipped；`ruff check .` All checks passed。
- V10 计划债务扫描修复：
  - 已修正 handoff 和 architecture 中残留的“当前 V9”口径。
  - 已把 V10 design 的实施前 `Migration Plan` 改成已执行的 implementation notes。
  - 已修正 Evidence Pack `original_query`，现在使用 `SearchPlan.original_query` 而不是提取后的 keyword。
  - 已修正 answer citation 过滤，混合相对路径和绝对路径结果时不把绝对路径写进 `/chat` answer。
  - `pytest tests\test_agent_harness_kernel.py tests\test_chat_api.py tests\test_evidence_pack.py`：42 passed。
  - `powershell -ExecutionPolicy Bypass -File scripts\verify.ps1`：通过；`pytest` 77 passed, 1 skipped；`ruff check .` All checks passed。
- 非 V10 历史代码债修复：
  - 已修正 V9 `hybrid_fuse` 默认阈值，强 embedding-only 命中可进入 hybrid 结果；`min_fused_score` 当前为 `0.35`。
  - 已把 AgentLoop 权限检查对象从底层 `search_code` 改为实际执行工具 `repo_rag`，并同步长期 `agent-loop-tool-execution` spec。
  - 已给 capability status 独立 route，英文状态问法不再进入 repo retrieval。
  - 已让普通英文问候避免误触发 repo_search，并清理测试中的部分 V8 命名噪音。
  - `pytest tests\test_repo_rag.py tests\test_agent_harness_kernel.py tests\test_chat_api.py`：50 passed。
  - `powershell -ExecutionPolicy Bypass -File scripts\verify.ps1`：通过；`pytest` 81 passed, 1 skipped；`ruff check .` All checks passed。
  - `openspec validate --all`：7 passed, 0 failed；`git diff --check`：通过，仅有 CRLF 换行提示。
- 已知剩余代码债：
  - `app/rag/evidence.py` 空 snippet 审计语义还可更干净，后续可改成 omitted 或跳过。
  - `app/harness/kernel.py` capability-status 仍是字符串规则集合，后续能力项增多时可抽成 classifier。
  - `app/rag/repo_rag.py` hybrid fusion 权重和阈值仍是硬编码常量，后续可参数化。
  - tests 中仍有少量历史阶段命名，可在测试清理时统一改成阶段无关命名。
- V10 前文档债扫描：
  - 已修正 `openspec/specs/README.md` 仍停留在 OpenSpec 初始化阶段的旧口径。
  - 已修正 `openspec/changes/README.md` 关于 legacy specs 迁移的旧口径。
  - 已修正 `docs/PROGRESS.md` 当前状态中的“当前 V4/V5 状态”措辞。
  - 已修正本 handoff V8 摘要中的“当前 V9 分支”措辞。

## 下一轮建议

1. 继续完成 V15 review、默认验证和 archive。
2. V15 收口前确认 `.harness/review_checklist.md` 中 contract、只读状态、DB 非初始化和 redaction gate 均已满足。
3. 继续保持默认验证：`openspec validate --all`、`powershell -ExecutionPolicy Bypass -File scripts\verify.ps1`、`git diff --check`。

后续路线已拆分：V10 做 Evidence Pack + Context Budget；V11 做 Grounded Answer / Model Provider Boundary；V12 做 Query Rewrite + Rerank；V13 做 Memory；V14 做 Long Task / ReAct Skeleton；V15 做 Assistant Control Surface；V16 做 Safe Patch Authoring；V17 做 Verification Runner；V18 做 Patch + Verify Loop；V19 做 Persistent Audit / Recovery；V20 做 Worktree Isolation。真实 subagents、connectors、notifications、heartbeat/cron 和 always-on assistant 放在 V20 之后单独规划。
旧 V8 archive 中保留的是当时路线记录，已被后续 V9/V10 路线重排 supersede；当前长期 docs/specs 以 README、PROGRESS、ARCHITECTURE 和长期 OpenSpec specs 为准。
