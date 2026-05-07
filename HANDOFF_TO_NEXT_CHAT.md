# 交接给下一轮 Chat

## 当前分支

```text
feature/v3-agent-loop
```

## 当前项目状态

RepoPilot 当前定位为面向代码仓库分析任务的可控 Code Agent Harness，不是替代通用 AI IDE 的编程助手。它已经完成 V1 Agent 服务入口、V2 安全只读仓库工具层和 V3 统一工具执行边界。`/chat` 现在会通过 `CodeAgent -> ToolExecutor -> search_code` 使用只读仓库搜索，并返回真实 `related_files` 和 `tool_calls`。

## 本轮重点

- 从已包含 V2 的集成点创建并切换到 `feature/v3-agent-loop`。
- 新增 V3 Agent Loop specs：
  - `specs/003-agent-loop/spec.md`
  - `specs/003-agent-loop/plan.md`
  - `specs/003-agent-loop/tasks.md`
- 更新 V3 实现阶段 harness：
  - `.harness/allowed_files.md`
  - `.harness/review_checklist.md`
- 新增轻量 `ToolExecutor`，当前只包装 `search_code`。
- 更新 `CodeAgent`，使用最小确定性关键词提取并调用 `ToolExecutor`。
- 更新 `/chat` 测试，覆盖 `UNIQUE_BUG_TOKEN` 命中、无命中、敏感文件不泄露和错误摘要脱敏。
- 更新 README、`docs/PROGRESS.md` 和 `docs/FEATURE_LIST.json`。
- 收尾同步项目定位：RepoPilot 是可控 Code Agent Harness，核心价值是可控、可审计、可验证、可扩展。
- 更新 `docs/ARCHITECTURE.md`，将当前链路同步为 `API -> ChatService -> CodeAgent -> ToolExecutor -> file_tools -> Trace`。

## 已验证

```text
powershell -ExecutionPolicy Bypass -File scripts/verify.ps1
pytest: 16 passed
ruff check .: All checks passed
```

## 下一轮建议

下一轮建议：

1. Review V3 是否符合最小范围和 harness allowed files。
2. 如继续路线图，进入 V4 前先更新 allowed files。
3. V4 可考虑基于 markdown 的 Skill Loader，或先进入 V5 trace/tool audit 扩展。
4. 保持高风险能力统一经过 `ToolExecutor` 增量加入。
5. 不要把 PermissionPolicy、ApprovalGate、SandboxRunner、eval、Reflection、RAG 或 Memory 写成已实现。

## 不要做

- 不接真实 LLM。
- 不自动修改代码。
- 不执行 shell 工具。
- 不加入复杂多 Agent。
- 不提前做 RAG、Memory、Reflection 或 eval。
- 不提前实现 PermissionPolicy、ApprovalGate 或 SandboxRunner。
