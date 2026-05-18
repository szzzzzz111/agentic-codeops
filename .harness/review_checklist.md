# 当前 Review 清单

当前活跃开发阶段：V6 Agent Harness Kernel + Router Kernel。

检查项：

- [ ] 当前变更有对应 OpenSpec change：`v6-agent-harness-kernel`。
- [ ] `.harness/allowed_files.md` 已更新为当前阶段写入边界。
- [ ] 变更只修改 `.harness/allowed_files.md` 列出的文件。
- [ ] 变更没有恢复旧 `specs/00x-*` 作为规格入口。
- [ ] V6 只建立 RequestRouter、ToolRegistry、AgentLoop 和 TraceEvent 的最小骨架。
- [ ] V6 明确定义 `AgentLoopRequest`、`RouteDecision`、`ToolSpec`、`TraceEvent` 和内部 `AgentLoopResult` 的最小 contract。
- [ ] `AgentLoop` 调用工具前先通过 `ToolRegistry` 校验工具存在、只读和风险等级。
- [ ] `/chat` 响应不新增顶层字段，继续使用 `answer`、`related_files`、`tool_calls`。
- [ ] 当前 V6 仍不接真实 LLM、不执行 skill、不做 RAG/Memory/Reflection/eval。
- [ ] 当前 V6 不实现 ProviderAdapter、ContextBuilder、SkillRegistry 或 SessionStore 的运行时代码。
- [ ] 运行时仓库搜索仍经过 `ToolExecutor`，且不得绕过 registry gate。
- [ ] 未引入 PostgreSQL、Milvus、Elasticsearch、Kafka 等重依赖。
- [ ] 已先写失败测试并观察失败，再实现代码。
- [ ] 已运行 `openspec validate v6-agent-harness-kernel`。
- [ ] 已运行 `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`，或说明无法运行的原因。
- [ ] 已运行 `git diff --check`。
