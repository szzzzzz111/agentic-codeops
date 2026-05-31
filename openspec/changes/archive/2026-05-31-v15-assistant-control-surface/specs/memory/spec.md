# memory Specification

## ADDED Requirements

### Requirement: Memory 提供只读控制面摘要

系统 SHALL 为 Assistant Control Surface 提供只读 Memory 摘要。摘要 MAY 包含 PREF、LTM 和当前 STM 的数量。摘要 MUST NOT 包含完整 memory value，MUST NOT 暴露本机绝对路径或 DB 路径。

#### Scenario: 控制面读取 Memory 摘要不创建 DB

- **WHEN** Assistant Control Surface 请求读取 Memory 摘要，且 `.repopilot/memory.sqlite3` 不存在
- **THEN** 系统返回 PREF/LTM 计数为 0 的摘要
- **AND** 系统 MUST NOT 创建 `.repopilot/` 目录或 `memory.sqlite3`
