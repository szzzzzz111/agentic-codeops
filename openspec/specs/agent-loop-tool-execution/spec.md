# agent-loop-tool-execution Specification

## Purpose

记录已实现的最小确定性 Agent Loop 和工具执行边界：`CodeAgent` 提取可搜索关键词，通过 `ToolExecutor` 调用只读 `search_code`，从真实搜索结果生成 `related_files` 和安全 `tool_calls` 摘要，不接真实 LLM、不修改代码、不执行 shell、不引入 RAG、Memory、Reflection、eval 或复杂多 Agent。
## Requirements
### Requirement: Agent Loop 使用确定性关键词搜索

当前 `CodeAgent` 行为 MUST 使用最小确定性关键词提取规则，并且 MUST NOT 依赖真实 LLM。

#### Scenario: 消息中包含搜索 token

- **WHEN** 聊天消息包含明确可搜索 token，例如 `UNIQUE_BUG_TOKEN`
- **THEN** Agent 使用该 token 作为搜索关键词

### Requirement: 工具调用经过 ToolExecutor

系统 SHALL 让 Agent 的仓库搜索先经过 `ToolExecutor`，再调用具体文件工具。

#### Scenario: 搜索工具调用

- **WHEN** `CodeAgent` 为 `/chat` 执行仓库搜索
- **THEN** 它通过 `ToolExecutor` 调用 `search_code`

### Requirement: 聊天响应从真实搜索结果生成 related_files

系统 SHALL 从安全搜索结果填充 `related_files`，并在无命中时保持响应稳定。

#### Scenario: 搜索命中

- **WHEN** 安全仓库搜索找到匹配文件
- **THEN** `/chat` 在 `related_files` 中返回去重后的相对文件路径

#### Scenario: 搜索无命中

- **WHEN** 安全仓库搜索没有找到匹配文件
- **THEN** `/chat` 返回空 `related_files` 列表且响应仍成功

### Requirement: 工具调用摘要安全

系统 SHALL 返回包含工具名、参数摘要、状态和结果数量的工具调用摘要，并且 MUST NOT 泄露完整文件内容、完整搜索结果或本机绝对路径。

#### Scenario: 搜索调用摘要

- **WHEN** `/chat` 调用仓库搜索
- **THEN** `tool_calls` 包含 `search_code` 摘要、关键词、状态和结果数量
- **AND** 摘要不包含完整文件内容或本机绝对路径

### Requirement: Agent Loop 不包含未来高风险能力

当前 Agent Loop MUST NOT 修改代码、执行 shell 命令、使用 RAG、使用 Memory、执行 Reflection、运行 eval 或使用复杂多 Agent 编排。

#### Scenario: 当前聊天行为

- **WHEN** 用户发送聊天请求
- **THEN** 系统只执行当前只读搜索行为

