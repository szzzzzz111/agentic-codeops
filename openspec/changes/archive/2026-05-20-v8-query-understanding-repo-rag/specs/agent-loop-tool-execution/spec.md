# agent-loop-tool-execution Delta

## MODIFIED Requirements

### Requirement: 工具调用经过 ToolRegistry、PermissionPolicy、ApprovalGate 和 ToolExecutor

系统 SHALL 继续使用 `ToolRegistry` 记录工具规格元数据，并在 repo-local 检索前通过 `PermissionPolicy` 和 `ApprovalGate`。V8 的 repo-local lexical RAG MUST 继续遵守 V7 的权限/审批边界；权限或审批失败时 MUST NOT 执行 repo 检索。

`AgentLoop` 在允许执行后 SHALL 使用 Query Understanding 产生的 `SearchPlan` 执行 repo-local lexical RAG。repo-local lexical RAG 的 `tool_calls[].tool_name` MUST 为 `repo_rag`，并且 `tool_calls` MUST 继续返回结构化审计摘要，但 MUST NOT 包含完整文件内容、本机绝对路径或新的 `/chat` 顶层 trace 字段。

#### Scenario: 允许的只读检索执行 lexical repo RAG

- **WHEN** `search_code` 已注册、只读、风险等级为 `low` 且 `requires_approval` 为 `False`
- **THEN** `PermissionPolicy` 返回 `allow`
- **AND** `AgentLoop` 执行 query understanding 和 lexical repo RAG
- **AND** `tool_calls` 中的 lexical repo RAG 审计条目使用 `tool_name=repo_rag`
- **AND** `related_files` 只包含相对 repo 路径
- **AND** `/chat` 顶层响应字段保持不变
