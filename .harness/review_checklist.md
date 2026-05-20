# 当前 Review 清单

当前活跃阶段：V8 `v8-query-understanding-repo-rag`。

- [ ] OpenSpec change 存在并通过 `openspec validate v8-query-understanding-repo-rag`。
- [ ] `.harness/allowed_files.md` 已限定 V8 写入边界。
- [ ] V8 明确是非向量化 lexical repo RAG，不实现 embedding、Milvus、Elasticsearch、PgVector、Qdrant。
- [ ] Query Understanding 是 deterministic 实现，不调用 LLM rewrite 或 LLM intent classifier。
- [ ] Lexical retrieval 返回 citation，且 citation 只包含相对 repo 路径和行号。
- [ ] `/chat` 顶层响应字段仍为 `trace_id`、`answer`、`related_files`、`tool_calls`。
- [ ] 参考项目只写成规划资料，没有写成当前 runtime dependency 或已实现能力。
- [ ] 现有 V7 权限/审批边界仍在 repo 检索前生效。
- [ ] 已运行 `pytest`、`ruff check .`、`powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`、`openspec validate --all` 和 `git diff --check`，或说明无法运行的原因。
