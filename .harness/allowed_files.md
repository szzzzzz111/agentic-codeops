# 当前 Harness 写入边界

当前活跃阶段：无。

V15 Assistant Control Surface 已归档到 `openspec/changes/archive/2026-05-31-v15-assistant-control-surface/`，长期 specs 已同步。下一阶段开始前必须先创建新的 OpenSpec change，并同步本文件和 `.harness/review_checklist.md`。

## 当前允许修改

- `docs/PROGRESS.md`
- `HANDOFF_TO_NEXT_CHAT.md`
- `.harness/allowed_files.md`
- `.harness/review_checklist.md`
- `README.md`
- `docs/ARCHITECTURE.md`
- `docs/FEATURE_LIST.json`
- `scripts/check_stage_docs.ps1`（仅限归档后阶段漂移规则）
- `scripts/check_stage_closeout.ps1`（仅限归档后阶段收尾验证规则）
- `openspec/specs/**`
- `openspec/changes/archive/**`

## 禁止修改

- 暂无 active stage 时，不得修改运行时代码、测试或新增功能。
- 不恢复旧 `specs/00x-*` 作为规格入口。
- 不把 OpenSpec、Superpowers、MCP、plugin 或参考项目写成 RepoPilot runtime 能力。
- 不绕过 `ToolExecutor(repo_rag)`、`PermissionPolicy`、`ApprovalGate` 或安全文件工具边界。
- 不默认接入 Milvus、Elasticsearch、PgVector、Qdrant、真实外部 embedding 服务、模型下载、tokenizer 依赖或持久化向量索引。
- 后续不得把真实 LLM rewrite/rerank、向量 memory、自动 memory 总结、context compression、SandboxRunner、skill execution、后台任务、自动循环执行、真实 subagent orchestration 或 worktree automation 写成已实现，除非新阶段明确开放。
- 不让默认验证依赖真实网络、真实 API key 或真实模型输出。
