# 当前 Harness 写入边界

当前活跃阶段：无。V9 `v9-embedding-hybrid-search` 已实现、提交并归档。

允许修改：

- 无活跃阶段默认不修改运行时代码、测试或长期文档。
- 新阶段开始前必须先创建 OpenSpec change，并同步 `.harness/allowed_files.md` 和 `.harness/review_checklist.md`。

禁止修改：

- 不恢复旧 `specs/00x-*` 作为规格入口。
- 不把参考项目写成 RepoPilot runtime dependency 或当前能力，除非新阶段 spec 明确开放。
- 不实现未进入 active OpenSpec change 的新 runtime 能力。
- 不新增 `/chat` 必需顶层字段，除非新阶段 spec 明确要求。
- 不默认接入 Milvus、Elasticsearch、PgVector、Qdrant、真实外部 embedding 服务或模型下载，除非新阶段 spec 明确要求。
- 不实现 LLM query rewrite、LLM rerank、grounded answer、model provider、memory、context compression、SandboxRunner、skill execution 或多 agent orchestration，除非新阶段 spec 明确要求。
