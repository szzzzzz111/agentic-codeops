# 交接给下一轮 Chat

## 分支状态

```text
当前工作分支：main
当前基线分支：main
当前活跃 OpenSpec change：无
```

## 当前项目状态

RepoPilot 当前定位为面向代码仓库分析任务的可控 Code Agent Harness，不是替代通用 AI IDE 的编程助手。V1-V7 已完成并进入长期规格/归档历史；当前暂无活跃开发阶段。

当前主链路：

```text
API -> ChatService(trace_id) -> CodeAgent -> AgentLoop -> ToolRegistry -> PermissionPolicy -> ApprovalGate -> ToolExecutor -> file_tools
```

`/chat` 顶层响应仍保持现有 contract：`trace_id`、`answer`、`related_files`、`tool_calls`。V7 的权限和审批审计只保留在内部 `trace_events_internal`，不作为 `/chat` 顶层字段暴露。

## 本轮完成

- 创建并实现 V7：`v7-permission-approval-gate`。
- 提交 V7：`7f1fc86 Add V7 permission approval gate`。
- 合并到 `main`：`Merge V7 permission approval gate`。
- 同步长期 spec：`openspec/specs/agent-loop-tool-execution/spec.md`。
- 归档 OpenSpec change：`openspec/changes/archive/2026-05-19-v7-permission-approval-gate/`。
- 恢复无活跃阶段 harness：
  - `.harness/allowed_files.md`
  - `.harness/review_checklist.md`

## V7 边界

已实现：

- `ToolSpec.requires_approval`
- `PermissionDecision`
- `PermissionPolicy`
- 最小 `ApprovalGate`
- 权限优先级：未注册、非只读或非 `low` 风险 -> `deny`；否则 `requires_approval=True` -> `ask`；否则 -> `allow`。
- `ToolRegistry` 只登记和读取 `ToolSpec`，不保留独立 allow/deny gate。
- `AgentLoop` 负责记录 `permission_checked`、`tool_rejected` 和 `approval_required` trace event。
- `related_files` 只返回相对仓库路径，不返回本机绝对路径。

V7 不做：

- 不实现真实审批 UI。
- 不持久化审批记录。
- 不新增写文件、删文件或 shell 工具。
- 不实现 SandboxRunner。
- 不接真实 LLM。
- 不执行 skill。
- 不做 RAG、Memory、Reflection、eval、复杂多 Agent 或长任务 Agent。
- 不新增 `/chat` 顶层响应字段。

## 本轮验证

- `openspec validate v7-permission-approval-gate`：通过。
- `pytest tests/test_agent_harness_kernel.py`：16 passed。
- `pytest tests/test_chat_api.py`：6 passed。
- `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`：通过。
  - `pytest`：46 passed, 1 skipped。
  - `ruff check .`：All checks passed。
- `git diff --check`：通过，仅有 CRLF 换行提示。
- `openspec validate --all`：通过。

## 下一轮建议

1. 若继续开发，先规划 V8：Repo RAG Engineering。
2. 新阶段开始前同步 `.harness/allowed_files.md` 和 `.harness/review_checklist.md`。
3. 继续避免把真实审批流程、SandboxRunner、RAG、Memory、skill execution 或复杂多 Agent 提前塞进非对应阶段。
