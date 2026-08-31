# verified-patch-promotion Specification

## Purpose

定义将已验证 retained patch worktree 受控提升到主工作区的 V25 边界，并明确 promotion 的资格校验、
受控写入、事务回滚、终态限制与脱敏审计责任。
## Requirements
### Requirement: Promotion Is Explicit, Scoped, And Fail-Closed

系统 SHALL allow promotion only for the current `user_id + repo_key` scoped retained worktree whose worktree lifecycle is `verification_succeeded` and whose patch status is `applied_in_worktree`. It MUST check main workspace cleanliness, main `HEAD == base_commit`, expected worktree path, Git registry/lock, linked-worktree ownership, retained worktree `HEAD == base_commit`, stored diff hash, and target content integrity. Any exception or mismatch MUST fail before main workspace writes.

Promotion preflight MUST use the shared hardened Git metadata runner for main workspace and retained worktree metadata reads. Metadata timeout, stdout oversize, reader failure, non-zero exit, malformed output, or exception MUST fail closed before promotion begins and MUST NOT expose raw Git output.

#### Scenario: Ineligible worktree is rejected

- **WHEN** a retained worktree is not `verification_succeeded`
- **THEN** promotion fails before any main workspace write

#### Scenario: Oversize metadata blocks promotion

- **WHEN** a Git metadata command used by promotion preflight exceeds the configured output cap
- **THEN** promotion fails closed before `patch_apply`
- **AND** no raw Git output is exposed

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
