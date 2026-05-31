# 当前 Harness 写入边界

当前活跃阶段：V15 Assistant Control Surface。

V15 `v15-assistant-control-surface` 只允许实现 `/chat` 内的只读助手控制面：聚合当前能力、Memory 摘要和 Long Task 摘要；不新增 API，不新增 `/chat` 顶层字段，不执行 repo_rag，不写 memory，不创建任务，不隐式初始化 `.repopilot` DB。

## 当前允许修改

- `app/assistant/**`
- `app/harness/kernel.py`
- `app/memory/manager.py`
- `app/memory/store.py`
- `app/longtask/manager.py`
- `app/longtask/store.py`
- `tests/test_assistant_control_surface.py`
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
- `openspec/changes/v15-assistant-control-surface/**`
- `openspec/changes/archive/**`

## 禁止修改

- V15 不新增 `/status`、`/tasks` 或其他公开 API。
- V15 不新增 `/chat` 必需或可选顶层字段。
- V15 控制面状态请求不得调用 `repo_rag`，不得进入 PermissionPolicy / ApprovalGate 工具调用链路。
- V15 控制面状态请求不得写 memory、创建/恢复/暂停/补充/归档 Long Task，或隐式初始化 `.repopilot/`、`memory.sqlite3`、`tasks.sqlite3`。
- 不恢复旧 `specs/00x-*` 作为规格入口。
- 不把 OpenSpec、Superpowers、MCP、plugin 或参考项目写成 RepoPilot runtime 能力。
- 不绕过 `ToolExecutor(repo_rag)`、`PermissionPolicy`、`ApprovalGate` 或安全文件工具边界。
- 不默认接入 Milvus、Elasticsearch、PgVector、Qdrant、真实外部 embedding 服务、模型下载、tokenizer 依赖或持久化向量索引。
- 后续不得把真实 LLM rewrite/rerank、向量 memory、自动 memory 总结、context compression、SandboxRunner、skill execution、后台任务、自动循环执行、真实 subagent orchestration 或 worktree automation 写成已实现，除非新阶段明确开放。
- 不让默认验证依赖真实网络、真实 API key 或真实模型输出。
