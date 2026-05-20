# 当前 Harness 写入边界

当前活跃阶段：V9 `v9-embedding-hybrid-search`。

允许修改：

- V9 OpenSpec artifacts：
  - `openspec/changes/v9-embedding-hybrid-search/**`
- V9 运行时代码与测试：
  - `app/rag/**`
  - `app/tools/tool_executor.py`
  - `app/harness/kernel.py`
  - `tests/test_query_understanding.py`
  - `tests/test_repo_rag.py`
  - `tests/test_agent_harness_kernel.py`
  - `tests/test_chat_api.py`
- V9 文档和验收清单：
  - `README.md`
  - `docs/ARCHITECTURE.md`
  - `docs/PROGRESS.md`
  - `docs/FEATURE_LIST.json`
  - `HANDOFF_TO_NEXT_CHAT.md`
  - `.harness/allowed_files.md`
  - `.harness/review_checklist.md`

禁止修改：

- 不恢复旧 `specs/00x-*` 作为规格入口。
- 不把参考项目写成 RepoPilot runtime dependency 或当前能力，除非 V9 spec 明确开放。
- 不实现 V9 scope 之外的新 runtime 能力。
- 不新增 `/chat` 必需顶层字段。
- 不默认接入 Milvus、Elasticsearch、PgVector、Qdrant、真实外部 embedding 服务或模型下载。
- 不实现 LLM query rewrite、LLM rerank、grounded answer、model provider、memory、context compression、SandboxRunner、skill execution 或多 agent orchestration。
