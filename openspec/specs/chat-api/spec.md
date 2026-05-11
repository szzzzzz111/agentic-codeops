# chat-api Specification

## Purpose
TBD - created by archiving change migrate-legacy-specs-to-openspec. Update Purpose after archive.
## Requirements
### Requirement: 聊天接口接收可追踪请求

系统 SHALL 暴露 `POST /chat` 作为 Agent 服务入口。请求 MUST 包含 `user_id`、`session_id`、`message` 和 `repo_path`。

#### Scenario: 有效聊天请求

- **WHEN** 客户端发送包含 `user_id`、`session_id`、`message` 和 `repo_path` 的有效 `POST /chat` 请求
- **THEN** 系统使用稳定的聊天响应 schema 返回成功响应

### Requirement: 聊天响应包含审计字段

系统 SHALL 在每个成功聊天响应中返回 `trace_id`、`answer`、`related_files` 和 `tool_calls`。

#### Scenario: Trace 响应结构

- **WHEN** 聊天请求成功完成
- **THEN** 响应包含以 `trace_` 开头的 `trace_id`
- **AND** 响应包含 `answer`、`related_files` 和 `tool_calls`

### Requirement: Trace 标识每次请求唯一

系统 SHALL 为每次聊天请求生成不同的请求级 `trace_id`。

#### Scenario: 连续请求

- **WHEN** 连续发送两次聊天请求
- **THEN** 两次响应中的 `trace_id` 不相同

### Requirement: API 层保持轻量

API 层 MUST 只负责 HTTP 路由和 schema 处理，不直接实现仓库搜索、工具执行或 Agent 决策。

#### Scenario: 聊天编排边界

- **WHEN** `/chat` 处理请求
- **THEN** 请求编排通过 Service 和 Agent 层完成，而不是把工具逻辑写进 router

