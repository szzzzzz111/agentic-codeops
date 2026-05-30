# chat-api Specification

## Purpose

记录已实现的 `/chat` 服务入口边界：接收可追踪聊天请求，返回稳定响应 schema 和审计字段，并保持 API 层只负责 HTTP 路由与 schema 处理，不直接实现仓库搜索、工具执行、grounded answer 或 Agent 决策。
## Requirements
### Requirement: 聊天接口接收可追踪请求

系统 SHALL 暴露 `POST /chat` 作为 Agent 服务入口。请求 MUST 包含 `user_id`、`session_id`、`message` 和 `repo_path`。

#### Scenario: 有效聊天请求

- **WHEN** 客户端发送包含 `user_id`、`session_id`、`message` 和 `repo_path` 的有效 `POST /chat` 请求
- **THEN** 系统使用稳定的聊天响应 schema 返回成功响应

### Requirement: 聊天响应包含审计字段

系统 SHALL 在每个成功聊天响应中返回 `trace_id`、`answer`、`related_files` 和 `tool_calls`。`answer` MAY 由 grounded answer pipeline 基于预算内仓库证据生成，也 MAY 在明确 memory command 或 Long Task command 命中时返回确认、状态或步骤摘要。系统 MUST NOT 为 V14 新增必需 `/chat` 顶层响应字段。

#### Scenario: Long Task 不改变响应 schema

- **WHEN** `/chat` 处理 Long Task 创建、查看、列出、暂停、恢复、补充、reopen 或归档命令
- **THEN** Long Task 结果 MUST 写入现有 `answer` 字段
- **AND** 响应 MUST 继续只要求 `trace_id`、`answer`、`related_files` 和 `tool_calls`
- **AND** `tool_calls` MUST NOT 包含完整 scratch、完整 ReAct trace、完整 provider output、DB 路径、本机绝对路径或内部 trace

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

