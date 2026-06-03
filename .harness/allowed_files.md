# 当前 Harness 写入边界

当前活跃阶段：V17 Verification Runner。

V17 规划 change：`openspec/changes/v17-verification-runner/`。本阶段只实现明确验证请求下的白名单验证命令执行，并通过权限、审批和 `ToolExecutor` 边界返回截断脱敏摘要。

## 当前允许修改

- `openspec/changes/v17-verification-runner/**`
- `.harness/allowed_files.md`
- `.harness/review_checklist.md`
- `app/verification/**`
- `app/harness/kernel.py`
- `app/tools/tool_executor.py`
- `tests/test_verification_runner.py`
- `tests/test_agent_harness_kernel.py`
- `tests/test_chat_api.py`
- `README.md`
- `docs/ARCHITECTURE.md`
- `docs/PROGRESS.md`
- `docs/FEATURE_LIST.json`
- `HANDOFF_TO_NEXT_CHAT.md`

## 禁止修改

- 未验证 V17 OpenSpec change 前，不得开始新的运行时代码实现。
- 不恢复旧 `specs/00x-*` 作为规格入口。
- 不把 OpenSpec、Superpowers、MCP、plugin 或参考项目写成 RepoPilot runtime 能力。
- 不绕过 `ToolExecutor(repo_rag)`、`PermissionPolicy`、`ApprovalGate` 或安全文件工具边界。
- 不新增 `/chat` 顶层字段，不新增公开 `/patches`、`/status` 或 `/tasks` API。
- 不开放任意 shell 命令、用户自定义验证参数、管道、重定向或环境变量注入。
- 不让 API handler、AgentLoop 或 parser 直接调用 subprocess；验证执行只能通过 `ToolExecutor.verification_run(...)`。
- 不把完整 diff 文本、完整 Evidence Pack、完整 provider prompt/output、本机绝对路径、DB 路径或 API key 暴露到公开响应。
- 不把完整 stdout、完整 stderr、完整 internal trace、环境变量或本机绝对路径暴露到公开验证响应。
- 不默认接入 Milvus、Elasticsearch、PgVector、Qdrant、真实外部 embedding 服务、模型下载、tokenizer 依赖或持久化向量索引。
- 后续不得把真实 LLM rewrite/rerank、向量 memory、自动 memory 总结、context compression、SandboxRunner、skill execution、后台任务、自动循环执行、真实 subagent orchestration 或 worktree automation 写成已实现，除非新阶段明确开放。
- V17 不自动在 patch apply 后运行验证，不根据验证失败自动生成 patch，不持久化 verification result，不创建 worktree，不自动 commit/push。
- 不让默认验证依赖真实网络、真实 API key 或真实模型输出。
