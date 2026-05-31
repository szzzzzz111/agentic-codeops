# 当前 Harness 写入边界

当前活跃阶段：V16 Safe Patch Authoring。

V16 目标是在现有 repo evidence / grounded answer 边界后生成可审查 patch proposal，并在用户明确确认后通过受控写入工具 apply。V16 不运行测试命令、不自动 commit、不创建 worktree、不执行 shell。

## 当前允许修改

- `app/harness/kernel.py`
- `app/tools/tool_executor.py`
- `app/tools/file_tools.py`
- `app/patching/**`
- `app/providers/**`
- `tests/test_patch_authoring.py`
- `tests/test_agent_harness_kernel.py`
- `tests/test_chat_api.py`
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
- `openspec/changes/v16-safe-patch-authoring/**`
- `openspec/changes/archive/**`

## 禁止修改

- V16 不得运行测试命令、自动 commit、创建 branch/worktree、执行 shell 或实现 Verification Runner。
- 不恢复旧 `specs/00x-*` 作为规格入口。
- 不把 OpenSpec、Superpowers、MCP、plugin 或参考项目写成 RepoPilot runtime 能力。
- 不绕过 `ToolExecutor(repo_rag)`、`PermissionPolicy`、`ApprovalGate` 或安全文件工具边界。
- 不绕过 `ToolRegistry -> PermissionPolicy -> ApprovalGate -> ToolExecutor` 执行 `patch_apply`。
- 不新增 `/chat` 顶层字段，不新增公开 `/patches`、`/status` 或 `/tasks` API。
- 不把完整 diff 文本、完整 Evidence Pack、完整 provider prompt/output、本机绝对路径、DB 路径或 API key 暴露到公开响应。
- 不默认接入 Milvus、Elasticsearch、PgVector、Qdrant、真实外部 embedding 服务、模型下载、tokenizer 依赖或持久化向量索引。
- 后续不得把真实 LLM rewrite/rerank、向量 memory、自动 memory 总结、context compression、SandboxRunner、skill execution、后台任务、自动循环执行、真实 subagent orchestration 或 worktree automation 写成已实现，除非新阶段明确开放。
- 不让默认验证依赖真实网络、真实 API key 或真实模型输出。
