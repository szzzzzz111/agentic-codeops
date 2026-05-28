# 当前 Harness 写入边界

当前活跃阶段：暂无。

V13 `v13-memory` 已实现并归档到 `openspec/changes/archive/2026-05-28-v13-memory/`。下一阶段开始前，必须先创建新的 OpenSpec change，并重新同步本文件与 `.harness/review_checklist.md`。

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
