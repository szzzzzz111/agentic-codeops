# 当前 Review 清单

当前活跃阶段：V9 `v9-embedding-hybrid-search`。

- [ ] `openspec validate v9-embedding-hybrid-search` 通过。
- [ ] `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1` 通过，或说明无法运行的原因。
- [ ] `git diff --check` 通过。
- [ ] `docs/PROGRESS.md` 和 `HANDOFF_TO_NEXT_CHAT.md` 反映当前 V9 阶段状态。
- [ ] V9 OpenSpec proposal/design/tasks/spec delta 已创建并通过校验。
- [ ] 未恢复旧 `specs/00x-*` 作为规格入口。
- [ ] 未把 OpenSpec、Superpowers、MCP、plugin 或参考项目写成 RepoPilot runtime 能力，除非新阶段 spec 明确开放。
- [ ] V9 保留 lexical retrieval 作为一等通道，没有用 embedding 替换 lexical。
- [ ] V9 默认 embedding provider 不依赖网络、密钥、模型下载或外部服务。
- [ ] V9 没有默认引入 Milvus、Elasticsearch、PgVector、Qdrant 或外部向量数据库。
- [ ] V9 没有实现 LLM query rewrite、LLM rerank、grounded answer、model provider、memory、context compression、SandboxRunner、skill execution 或多 agent orchestration。
- [ ] `/chat` 顶层 contract 仍只要求 `trace_id`、`answer`、`related_files`、`tool_calls`。
