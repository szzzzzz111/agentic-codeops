# 当前 Review 清单

当前阶段：V7 `v7-permission-approval-gate`

- [ ] 当前变更有对应 OpenSpec change：`openspec/changes/v7-permission-approval-gate/`。
- [ ] `.harness/allowed_files.md` 已更新为 V7 写入边界。
- [ ] 变更没有恢复旧 `specs/00x-*` 作为规格入口。
- [ ] OpenSpec、Superpowers、MCP、plugin 或外部 skill 没有被误写成 RepoPilot runtime 能力。
- [ ] `PermissionPolicy` 只输出 `allow`、`deny`、`ask`，且优先级为 deny > ask > allow。
- [ ] `ToolRegistry` 只登记和读取 `ToolSpec`，不保留独立 allow/deny gate。
- [ ] `ApprovalGate` 只消费权限结果，不实现真实审批 UI 或审批持久化。
- [ ] `AgentLoop` 负责记录 `permission_checked`、`tool_rejected` 和 `approval_required`。
- [ ] `deny` 和 `ask` 分支不调用 executor，`related_files=[]` 且 `tool_calls=[]`。
- [ ] `related_files` 不返回本机绝对路径。
- [ ] 权限和审批审计只记录在内部 `trace_events_internal`，没有新增 `/chat` 顶层 trace 字段。
- [ ] `chat_only` 不进入 permission/approval 链路，不记录 `permission_checked`。
- [ ] 未实现写文件、shell、SandboxRunner、LLM、RAG、Memory、Reflection、skill execution、eval 或复杂多 Agent。
- [ ] 已运行 `openspec validate v7-permission-approval-gate`。
- [ ] 已运行 `pytest tests/test_agent_harness_kernel.py` 和 `pytest tests/test_chat_api.py`。
- [ ] 已运行 `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`，或说明无法运行的原因。
- [ ] 已运行 `git diff --check`。
