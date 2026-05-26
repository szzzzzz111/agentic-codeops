# 当前 Harness 写入边界

当前活跃阶段：V11 `v11-grounded-answer-model-provider-boundary`。

本阶段目标是在 V10 Evidence Pack / Context Budget 之后增加 Grounded Answer / Model Provider Boundary，并保持 `/chat` 顶层响应 contract 不变。

## 当前允许修改

- `openspec/changes/v11-grounded-answer-model-provider-boundary/**`
- `openspec/specs/grounded-answer-model-provider/spec.md`
- `openspec/specs/agent-loop-tool-execution/spec.md`
- `openspec/specs/chat-api/spec.md`
- `openspec/specs/repo-query-understanding-rag/spec.md`
- `app/answering/**`
- `app/providers/**`
- `app/harness/kernel.py`
- `app/agents/code_agent.py`
- `pyproject.toml`
- `tests/test_model_provider.py`
- `tests/test_grounded_answer.py`
- `tests/test_agent_harness_kernel.py`
- `tests/test_chat_api.py`
- `.harness/allowed_files.md`
- `.harness/review_checklist.md`
- `README.md`
- `docs/ARCHITECTURE.md`
- `docs/PROGRESS.md`
- `docs/FEATURE_LIST.json`
- `HANDOFF_TO_NEXT_CHAT.md`

## 禁止修改

- 不恢复旧 `specs/00x-*` 作为规格入口。
- 不把 OpenSpec、Superpowers、MCP、plugin 或参考项目写成 RepoPilot runtime 能力。
- 不新增 `/chat` 必需顶层字段；V11 grounded answer 写入现有 `answer` 字段。
- 不绕过 `ToolExecutor(repo_rag)`、`PermissionPolicy`、`ApprovalGate` 或安全文件工具边界。
- 不默认接入 Milvus、Elasticsearch、PgVector、Qdrant、真实外部 embedding 服务、模型下载、tokenizer 依赖或持久化向量索引。
- 不实现 query rewrite、rerank、memory、context compression、SandboxRunner、skill execution 或多 agent orchestration。
- 不把小米 MiMo/Mino 写死为运行时主链路；真实 provider 只能作为 OpenAI-compatible provider 的显式配置。
- 不让默认验证依赖真实网络、真实 API key 或真实模型输出。
