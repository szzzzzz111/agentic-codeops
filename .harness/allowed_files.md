# 当前 Harness 写入边界

当前活跃阶段：V18 Patch + Verify Loop。

V18 目标是在 V16 Safe Patch Authoring 与 V17 Verification Runner 之间建立明确用户确认下的 apply 后 verify 闭环。实现前已创建 OpenSpec change：`openspec/changes/v18-patch-verify-loop/`。

## 当前允许修改

- `.harness/allowed_files.md`
- `.harness/review_checklist.md`
- `openspec/changes/v18-patch-verify-loop/**`
- `app/harness/kernel.py`
- `app/patching/**`
- `app/verification/**`
- `tests/test_patch_authoring.py`
- `tests/test_verification_runner.py`
- `tests/test_agent_harness_kernel.py`
- `tests/test_chat_api.py`
- `README.md`
- `docs/ARCHITECTURE.md`
- `docs/PROGRESS.md`
- `docs/FEATURE_LIST.json`
- `HANDOFF_TO_NEXT_CHAT.md`

## 禁止修改

- 不恢复旧 `specs/00x-*` 作为规格入口。
- 不把 OpenSpec、Superpowers、MCP、plugin 或参考项目写成 RepoPilot runtime 能力。
- 不新增 `/chat` 顶层字段，不新增公开 `/patches`、`/status`、`/tasks` 或 `/verification` API。
- 不绕过 `ToolExecutor(repo_rag / patch_apply / verification_run)`、`PermissionPolicy`、`ApprovalGate` 或安全文件工具边界。
- 不开放任意 shell 命令、用户自定义验证参数、targeted pytest、管道、重定向、环境变量注入或 `ruff --fix`。
- 不让 API handler、AgentLoop parser 或 patch parser 直接调用 subprocess；验证执行只能通过 `ToolExecutor.verification_run(...)`。
- 组合确认缺失 verification label、半解析、非法 label、附加参数或 shell 语法时，不得 apply patch。
- patch apply 失败、过期、hash mismatch、跨用户或跨 repo 时，不得生成 verification context，不得运行验证。
- verification context 不得复用 patch context；必须使用独立 `ToolInvocationContext(tool_name="verification_run", intent="verification_run", command_label=..., confirmed=True, scope_valid=...)`。
- 不把完整 diff 文本、完整 Evidence Pack、完整 provider prompt/output、本机绝对路径、DB 路径或 API key 暴露到公开响应。
- 不把完整 stdout、完整 stderr、完整 internal trace、环境变量或本机绝对路径暴露到公开验证响应。
- 不默认接入 Milvus、Elasticsearch、PgVector、Qdrant、真实外部 embedding 服务、模型下载、tokenizer 依赖或持久化向量索引。
- 不把真实 LLM rewrite/rerank、向量 memory、自动 memory 总结、context compression、SandboxRunner、skill execution、后台任务、自动循环执行、真实 subagent orchestration、Persistent Audit / Recovery 或 worktree automation 写成已实现。
- V18 不根据验证失败自动生成 patch，不自动再次 apply，不持久化 verification result，不创建 worktree，不自动 commit/push。
- 不让默认验证依赖真实网络、真实 API key 或真实模型输出。
