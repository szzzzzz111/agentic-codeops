# 当前 Harness 写入边界

当前活跃阶段：V8 `v8-query-understanding-repo-rag`。

允许修改：

- `openspec/changes/v8-query-understanding-repo-rag/**`
- `.harness/allowed_files.md`
- `.harness/review_checklist.md`
- `app/harness/kernel.py`
- `app/rag/**`
- `app/tools/tool_executor.py`
- `tests/test_query_understanding.py`
- `tests/test_repo_rag.py`
- `tests/test_agent_harness_kernel.py`
- `tests/test_chat_api.py`
- `README.md`
- `docs/ARCHITECTURE.md`
- `docs/PROGRESS.md`
- `docs/FEATURE_LIST.json`
- `HANDOFF_TO_NEXT_CHAT.md`

禁止修改：

- 不恢复旧 `specs/00x-*` 作为规格入口。
- 不把参考项目写成 RepoPilot runtime dependency 或当前能力。
- 不实现 embedding、Milvus、Elasticsearch、PgVector、Qdrant、LLM rewrite、rerank、memory、SandboxRunner、skill execution 或多 agent orchestration。
- 不新增 `/chat` 必需顶层字段。
