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

系统 SHALL 在每个成功聊天响应中返回 `trace_id`、`answer`、`related_files` 和 `tool_calls`。`answer` MAY 由 grounded answer pipeline 基于预算内仓库证据生成，也 MAY 在明确 memory command、Long Task command、Assistant Control Surface 状态请求、Patch proposal 请求、明确 patch apply 确认、明确 verification run 请求或明确 Patch + Verify Loop 组合确认命中时返回确认、状态、步骤摘要、助手控制面摘要、patch proposal、apply 结果、验证结果摘要或组合摘要。系统 MUST NOT 为 V18 新增必需或可选 `/chat` 顶层响应字段。

#### Scenario: Patch Verify Loop 不改变响应 schema

- **WHEN** `/chat` 处理合法 Patch + Verify Loop 组合确认
- **THEN** 组合结果摘要 MUST 写入现有 `answer` 字段
- **AND** 响应 MUST 继续只要求 `trace_id`、`answer`、`related_files` 和 `tool_calls`
- **AND** 响应 MUST NOT 包含完整 diff、完整 stdout、完整 stderr、本机绝对路径、DB 路径、环境变量、API key 或内部 trace

#### Scenario: Verification run 不改变响应 schema

- **WHEN** `/chat` 处理明确 verification run 请求
- **THEN** 验证结果摘要 MUST 写入现有 `answer` 字段
- **AND** 响应 MUST 继续只要求 `trace_id`、`answer`、`related_files` 和 `tool_calls`
- **AND** 响应 MUST NOT 包含完整 stdout、完整 stderr、本机绝对路径、DB 路径、环境变量、API key 或内部 trace

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

### Requirement: `/chat` Response Contract Remains Stable

系统 SHALL keep the existing `/chat` top-level response fields unchanged while adding V19 recovery/status behavior. Recovery/status answers MUST be returned through the existing `answer` field, with `related_files` and `tool_calls` preserving existing safe semantics.

V19 MUST NOT add a standalone audit API or new required/optional top-level `/chat` fields.

#### Scenario: Recovery answer uses existing contract

- **WHEN** the user asks for recent audit records or recovery status through `/chat`
- **THEN** the response still contains only the established top-level fields
- **AND** the recovery information is formatted in `answer`
- **AND** no full internal trace, DB path, full diff, full stdout/stderr, Evidence Pack, provider content, secret, or local absolute path is exposed

### Requirement: Worktree Results Reuse The Existing Chat Contract

系统 SHALL return worktree-backed patch results and worktree status answers through the existing `/chat` response contract. V20 MUST NOT add new required or optional top-level `/chat` fields.

Public worktree answers MAY include safe `worktree_id`, patch id, status summary, base commit, and verification summary. Public answers MUST NOT expose local absolute paths, `.git` paths, DB paths, or full Git output.

#### Scenario: Worktree-backed patch apply keeps contract

- **WHEN** `/chat` returns a worktree-backed patch result
- **THEN** the response still contains only `trace_id`, `answer`, `related_files`, and `tool_calls`
- **AND** `answer` may mention `worktree_id`
- **AND** `answer` MUST NOT expose the worktree filesystem path

### Requirement: Worktree Inventory And Inspection Reuse The Existing Chat Contract

系统 SHALL return V21 inventory and inspection through the existing `/chat.answer`. V21 MUST NOT add required or optional top-level `/chat` fields or a standalone worktree API.

`related_files` and `tool_calls` MUST remain empty for inventory / inspection because the flow does not use repo RAG or execution tools.

#### Scenario: Inspection answer keeps chat schema

- **WHEN** `/chat` returns a V21 inspection result
- **THEN** the response contains only `trace_id`, `answer`, `related_files`, and `tool_calls`
- **AND** bounded preview may appear only in `answer`
- **AND** `related_files` and `tool_calls` are empty

### Requirement: Worktree Re-verification Reuses The Existing Chat Contract

系统 SHALL return retained worktree re-verification results through the existing `/chat.answer` and safe `tool_calls` semantics. Re-verification MUST NOT add required or optional top-level `/chat` fields or a standalone verification/worktree API.

`related_files` MUST remain empty. Preflight failures MUST expose no verification tool call. Successful preflight MAY expose only the existing safe `verification_run` tool-call summary.

#### Scenario: Re-verification answer keeps chat schema

- **WHEN** `/chat` returns a retained worktree re-verification result
- **THEN** the response contains only `trace_id`, `answer`, `related_files`, and `tool_calls`
- **AND** it MUST NOT expose the trusted worktree execution path
