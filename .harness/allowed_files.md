# 当前 Harness 写入边界

当前活跃阶段：V13 `v13-memory`。

V13 目标是实现 repo-local SQLite-backed Memory 纵向切片，包含 PREF/LTM 持久化、进程内 STM、明确聊天指令和内部 memory audit。V13 plan review 已通过；本阶段允许按 OpenSpec change `v13-memory` 修改运行时代码、测试和文档。

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
- `app/memory/**`
- `app/harness/kernel.py`
- `app/agents/code_agent.py`
- `app/services/chat_service.py`
- `tests/test_memory.py`
- `tests/test_agent_harness_kernel.py`
- `tests/test_chat_api.py`
- `openspec/specs/**`
- `openspec/changes/v13-memory/**`
- `openspec/changes/archive/**`

## 禁止修改

- 不恢复旧 `specs/00x-*` 作为规格入口。
- 不把 OpenSpec、Superpowers、MCP、plugin 或参考项目写成 RepoPilot runtime 能力。
- 不在 V13 scope 外修改运行时代码或测试。
- 不新增 `/chat` 必需顶层字段。
- 不绕过 `ToolExecutor(repo_rag)`、`PermissionPolicy`、`ApprovalGate` 或安全文件工具边界。
- 不默认接入 Milvus、Elasticsearch、PgVector、Qdrant、真实外部 embedding 服务、模型下载、tokenizer 依赖或持久化向量索引。
- V12 已实现默认 deterministic query rewrite 和 deterministic rerank；后续不得把真实 LLM rewrite/rerank、memory、context compression、SandboxRunner、skill execution 或多 agent orchestration 写成已实现，除非新阶段明确开放。
- 不把小米 MiMo/Mino 写死为运行时主链路；真实 provider 只能作为 OpenAI-compatible provider 的显式配置。
- 不让默认验证依赖真实网络、真实 API key 或真实模型输出。
- Memory 只能写入 repo-local `.repopilot/` 本地状态目录；不得修改被分析仓库代码文件。
- Memory audit 不得暴露完整 memory value、本机绝对路径、DB 路径、完整 Evidence Pack 或模型输出。
