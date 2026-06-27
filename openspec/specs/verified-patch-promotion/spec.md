# verified-patch-promotion Specification

## Purpose

定义将已验证 retained patch worktree 受控提升到主工作区的 V25 边界。

## Requirements

### Requirement: Promotion Is Explicit, Scoped, And Fail-Closed

系统 SHALL 只接受精确命令 `confirm promote worktree <worktree_id>` 或
`确认提升 worktree <worktree_id>`。任何缺少确认、额外文本、不安全 id、路径、shell 语法、Git 参数或
模糊续写 MUST 整体拒绝且不 fall through。

Promotion MUST 只处理当前 `user_id + repo_key` scope 中 lifecycle 为
`verification_succeeded` 的 retained worktree，且关联 patch 状态为
`applied_in_worktree`。它 MUST 检查主工作区干净、主 `HEAD == base_commit`、预期 worktree
path、Git registry/lock、linked-worktree ownership、retained worktree `HEAD == base_commit`、stored diff
hash 和 target content integrity。任一异常或不一致 MUST 在主工作区写入前失败。

#### Scenario: Tampered retained content is rejected

- **WHEN** retained worktree 的 target content 不等于 stored controlled patch 的预期结果
- **THEN** promotion 拒绝且主工作区不变

### Requirement: Promotion Uses Stored Patch And Existing Harness

系统 SHALL 只以 stored controlled patch 为主工作区写入来源，并且只通过既有
`ToolRegistry`、`PermissionPolicy`、`ApprovalGate`、`ToolExecutor.patch_apply` 执行。
Worktree 文件 MUST NOT 被直接复制到主工作区。promotion MUST 使用独立的 promotion-safe context；
ordinary `applied_in_worktree` patch apply MUST 继续被拒绝。

#### Scenario: Verified promotion uses patch_apply

- **WHEN** scope 与完整性 preflight 全部通过
- **THEN** 主工作区写入通过 approval-gated `patch_apply` 执行
- **AND** 不复制 worktree 文件

### Requirement: Promotion State Is Transactional At The Harness Boundary

成功 promotion SHALL 将 patch 与 worktree 都转为 `promoted`。多文件 patch apply MUST stage
新内容和原始备份；staging 或 commit failure MUST 保持或恢复目标文件。状态持久化失败时，系统 MUST
通过同一受控 patch apply 路径回滚主工作区和 lifecycle，并以 journal 保留失败语义。

`promoted` 是 V25 的 retained terminal state：重复 promotion、re-verification、patch mutation 和
V23 disposal/reconciliation MUST 安全拒绝。promotion MUST NOT 删除 worktree、commit、merge、push、
创建 branch/PR、prune、后台 retry 或自动 repair。

#### Scenario: State persistence failure restores the workspace

- **WHEN** stored patch 已施加到主工作区但 lifecycle 状态无法完成
- **THEN** 系统以受控逆向 patch 恢复主工作区
- **AND** patch/worktree 不标记为 `promoted`

### Requirement: Promotion Is Auditable Without Public Contract Expansion

每个 recognized promotion attempt SHALL 尝试写入 scoped、redacted 的
`verified_patch_promotion` audit event，包含安全 confirmation/preflight/execution/error fields，且不包含
路径、Git/DB 原始输出、diff、patch body、文件内容、environment 或 secret。结果继续通过既有
`/chat.answer` 与 safe `tool_calls` 返回，不新增 `/chat` 顶层字段或 standalone API。

#### Scenario: Malformed promotion is auditable

- **WHEN** 用户发送 malformed promotion-like command
- **THEN** 系统记录 `confirmation=false` 的安全 audit event
- **AND** 不调用 patch apply 或后续路由
