# 当前 Harness 写入边界

当前活跃开发阶段：V6 Agent Harness Kernel + Router Kernel。

OpenSpec change：

- `openspec/changes/v6-agent-harness-kernel/`

本阶段允许修改：

- `.harness/allowed_files.md`
- `.harness/review_checklist.md`
- `openspec/changes/v6-agent-harness-kernel/proposal.md`
- `openspec/changes/v6-agent-harness-kernel/design.md`
- `openspec/changes/v6-agent-harness-kernel/tasks.md`
- `openspec/changes/v6-agent-harness-kernel/specs/agent-loop-tool-execution/spec.md`
- `openspec/changes/v6-agent-harness-kernel/specs/harness-development-workflow/spec.md`
- `app/agents/code_agent.py`
- `app/harness/__init__.py`
- `app/harness/kernel.py`
- `tests/test_agent_harness_kernel.py`
- `README.md`
- `docs/PROGRESS.md`
- `docs/FEATURE_LIST.json`
- `HANDOFF_TO_NEXT_CHAT.md`

本阶段禁止修改或实现：

- 不恢复旧 `specs/00x-*` 作为规格入口。
- 不修改 API schema，不新增 `/chat` 响应顶层字段。
- 不接入真实 LLM、RAG、Memory、Reflection、eval 或复杂多 Agent。
- 不实现 ProviderAdapter、ContextBuilder、SkillRegistry 或 SessionStore 的运行时代码。
- 不执行 skill，不把 skill 内容返回给用户，不自动把完整 skill 内容注入回答。
- 不新增写文件、删文件、shell 执行、PermissionPolicy、ApprovalGate 或 SandboxRunner。
- 不引入 PostgreSQL、Milvus、Elasticsearch、Kafka 等重依赖。
- 不绕过 `ToolExecutor` 增加运行时工具调用。
