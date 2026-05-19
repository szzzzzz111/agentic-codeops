## 1. Harness

- [x] 1.1 创建 `v7-permission-approval-gate` OpenSpec change。
- [x] 1.2 更新 `.harness/allowed_files.md`。
- [x] 1.3 更新 `.harness/review_checklist.md`。

## 2. OpenSpec

- [x] 2.1 编写 V7 proposal。
- [x] 2.2 编写 V7 design。
- [x] 2.3 编写 `agent-loop-tool-execution` spec delta。
- [x] 2.4 运行 `openspec validate v7-permission-approval-gate`。

## 3. Tests

- [x] 3.1 为默认 `search_code` 工具新增失败测试，确认低风险只读工具通过权限校验并执行搜索。
- [x] 3.2 为非只读、高风险和未注册工具新增失败测试，确认结果为 `deny` 且不调用 executor。
- [x] 3.3 为 `risk!="low"` 优先于 `requires_approval=True` 新增失败测试。
- [x] 3.4 为低风险只读但 `requires_approval=True` 新增失败测试，确认结果为 `ask`、固定回答、空 `related_files`、空 `tool_calls` 且不调用 executor。
- [x] 3.5 为 `chat_only` 新增回归断言，确认不记录 `permission_checked`。
- [x] 3.6 为 `/chat` 响应字段不新增 trace 字段保留回归测试。
- [x] 3.7 为异常绝对路径结果新增回归断言，确认 `related_files` 不返回本机绝对路径。

## 4. Implementation

- [x] 4.1 扩展 `ToolSpec`，新增 `requires_approval` 默认值。
- [x] 4.2 新增 `PermissionDecision`、`PermissionPolicy` 和 `ApprovalGate`。
- [x] 4.3 将 `AgentLoop` 工具调用前链路改为 registry lookup -> permission policy -> approval gate -> executor。
- [x] 4.4 实现 allow、deny、ask、chat_only 的固定响应和 trace 顺序。
- [x] 4.5 保持 `/chat` API schema 和安全摘要不变。
- [x] 4.6 移除 `ToolRegistry` 的独立 allow/deny gate helper，让权限状态统一由 `PermissionPolicy` 产出。
- [x] 4.7 过滤上游异常绝对路径，确保 `related_files` 只返回相对仓库路径。

## 5. Docs and Verification

- [x] 5.1 更新 `README.md`。
- [x] 5.2 更新 `docs/ARCHITECTURE.md`。
- [x] 5.3 更新 `docs/PROGRESS.md`。
- [x] 5.4 更新 `docs/FEATURE_LIST.json`。
- [x] 5.5 更新 `HANDOFF_TO_NEXT_CHAT.md`。
- [x] 5.6 运行 `pytest tests/test_agent_harness_kernel.py`。
- [x] 5.7 运行 `pytest tests/test_chat_api.py`。
- [x] 5.8 运行 `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`。
- [x] 5.9 运行 `git diff --check`。
