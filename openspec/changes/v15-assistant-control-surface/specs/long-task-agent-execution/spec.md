# long-task-agent-execution Specification

## ADDED Requirements

### Requirement: Long Task 提供只读控制面摘要

系统 SHALL 为 Assistant Control Surface 提供只读 Long Task 摘要。摘要 MAY 包含未归档任务数量，以及最近最多 3 个任务的 `task_id`、`status`、`title` 和当前或下一步标题。摘要 MUST NOT 包含完整 scratch、完整 ReAct trace、本机绝对路径或 DB 路径。

#### Scenario: 控制面读取 Long Task 摘要不创建 DB

- **WHEN** Assistant Control Surface 请求读取 Long Task 摘要，且 `.repopilot/tasks.sqlite3` 不存在
- **THEN** 系统返回未归档任务数量为 0 的摘要
- **AND** 系统 MUST NOT 创建 `.repopilot/` 目录或 `tasks.sqlite3`
