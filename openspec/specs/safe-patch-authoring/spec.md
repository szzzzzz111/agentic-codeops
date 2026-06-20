# safe-patch-authoring Specification

## Purpose
定义 RepoPilot 基于仓库证据生成 pending patch proposal 并在用户明确确认后通过受控 `patch_apply` 写入的边界。该能力要求 pending patch 按 user/repo 隔离、diff 在创建和应用前完成安全校验，并保持公开响应脱敏。
## Requirements
### Requirement: Patch proposal 由仓库证据约束

系统 SHALL 在明确 patch 请求时基于 repo evidence 生成 patch proposal。Patch proposal MUST 先经过现有 `repo_rag` / Evidence Pack 边界，MUST NOT 只凭模型自由生成。

默认应用装配 MUST 使用离线确定性的 fake Patch Authoring provider，并且 MUST NOT 生成真实 diff。仓库 MAY 提供可通过依赖注入使用的 `ModelPatchAuthoringProvider` 实现边界，但当前默认 `AgentLoop` / `PatchManager` 装配 MUST NOT 被描述为可通过现有 Model Provider 环境变量启用真实 patch proposal。未来若增加该装配，MUST 通过独立 change 定义配置、安全和验证边界。

任何注入的 Patch Authoring provider 返回结构化 JSON unified diff 时，系统 MUST 在创建 pending patch 前校验 schema、citation、路径和 diff。

#### Scenario: 默认 provider 不生成真实 diff

- **WHEN** 用户请求生成 patch proposal 且未显式配置真实 provider
- **THEN** 系统返回安全 fallback
- **AND** 系统 MUST NOT 创建 pending patch
- **AND** 系统 MUST NOT 修改文件

#### Scenario: Model Provider 环境配置不隐式启用 patch provider

- **WHEN** 应用只配置现有 `REPOPILOT_MODEL_PROVIDER` 等共享 Model Provider 环境变量
- **THEN** 默认 `PatchManager` 仍使用 fake Patch Authoring provider
- **AND** 系统 MUST NOT 声称真实 patch diff generation 已启用

#### Scenario: 注入的合法结构化 diff 创建 pending patch

- **WHEN** 调用方显式依赖注入 Patch Authoring provider 且其返回合法结构化 diff
- **THEN** 系统创建 pending patch
- **AND** 公开回答包含 patch 摘要、目标文件、patch id 和确认方式
- **AND** 公开回答 MUST NOT 暴露完整 diff 文本

### Requirement: Pending patch 使用 repo-local store

系统 SHALL 使用 repo-local `.repopilot/patches.sqlite3` 保存 pending patch metadata 和 diff。Pending patch MUST 按 `user_id + repo_key` 隔离，并保存 `patch_id`、`status`、`target_files`、`diff_text`、`diff_hash`、`summary`、`created_at`、`updated_at` 和 `expires_at`。

Pending patch 默认 24 小时过期。过期 patch MUST NOT apply，确认时系统 SHALL 将其标记为 `expired` 并返回安全失败摘要。

#### Scenario: Pending patch 跨用户不可确认

- **WHEN** 另一个 user_id 尝试确认 pending patch
- **THEN** 系统 MUST 拒绝 apply
- **AND** 系统 MUST NOT 修改文件

#### Scenario: Pending patch 过期

- **WHEN** 用户确认已过期 pending patch
- **THEN** 系统 MUST 标记 patch 为 `expired`
- **AND** 系统 MUST NOT 修改文件

### Requirement: Patch apply 必须明确确认

系统 SHALL 只接受明确确认语法应用 patch：`应用 patch <patch_id>`、`确认 patch <patch_id>`、`apply patch <patch_id>` 和 `confirm patch <patch_id>`。系统 MUST NOT 接受“可以”“继续”“就这样”等含糊表达作为 apply 确认。

V18 MAY 支持明确组合确认语法，将 pending patch apply 与白名单 verification run 串联。组合确认 MUST 同时包含有效 patch id 和有效 verification label；任一缺失或不安全时 MUST 拒绝整个组合请求，并且 MUST NOT apply patch。

#### Scenario: 含糊确认不触发 apply

- **WHEN** 用户发送 `可以`
- **THEN** 系统 MUST NOT 执行 `patch_apply`
- **AND** 系统 MUST NOT 修改文件

#### Scenario: 组合确认缺失验证标签不触发 apply

- **WHEN** 用户发送类似组合确认但只包含 patch id
- **THEN** 系统 MUST 拒绝组合请求
- **AND** 系统 MUST NOT 执行 `patch_apply`

### Requirement: Patch apply 只通过受控写入工具

系统 SHALL 只通过 `patch_apply` 执行 V16 写入。`patch_apply` MUST 只作用于 unified diff 中声明的 repo 内相对路径，MUST 拒绝路径穿越、绝对路径、repo 外路径、敏感文件、隐藏状态目录和二进制文件。

`patch_apply` MUST 先对所有目标文件和 hunks 完成 preflight，并在内存中生成新内容。任一 preflight 失败时 MUST NOT 写任何文件。多文件写入阶段发生 I/O 失败时，系统 MUST 尝试恢复已写文件的原始内容，并将 patch 标记为 `failed`。

#### Scenario: 多文件 preflight 失败不写入

- **WHEN** unified diff 中任一文件 context 不匹配
- **THEN** 系统 MUST 拒绝 apply
- **AND** 所有目标文件 MUST 保持原样

#### Scenario: 成功 apply

- **WHEN** pending patch 有效且用户明确确认
- **THEN** 系统通过 `patch_apply` 修改 diff 中的目标文件
- **AND** 系统 SHALL 将 patch 标记为 `applied`
- **AND** 系统 MUST NOT 运行测试、commit 或创建 worktree

### Requirement: Patch 公开响应脱敏

系统 SHALL 通过现有 `/chat.answer` 返回 patch proposal、patch id、确认提示和 apply 结果。系统 MUST NOT 为 V16 新增 `/chat` 顶层字段，MUST NOT 公开完整 diff 文本、完整 Evidence Pack、完整 provider prompt、完整 provider output、本机绝对路径、DB 路径或 API key。

#### Scenario: Patch proposal 保持 chat contract

- **WHEN** `/chat` 返回 patch proposal
- **THEN** 响应 MUST 继续只包含 `trace_id`、`answer`、`related_files` 和 `tool_calls`
- **AND** `answer` MUST NOT 包含完整 diff 文本

### Requirement: Patch Attempts Produce Persistent Audit Summaries

系统 SHALL record redacted persistent audit summaries for patch proposal, apply, failure, expiry, and combined patch/verify attempts when an audit store is available.

Patch audit summaries MAY include patch id, operation, status, target files, diff hash, changed-file counts, and safe error class. Patch audit summaries MUST NOT persist or expose the full unified diff, full Evidence Pack, provider prompt/output, DB path, local absolute path, API key, or secret.

#### Scenario: Patch apply audit summary is safe

- **WHEN** a pending patch is applied or fails to apply
- **THEN** the persistent audit event records safe patch identifiers and status
- **AND** it MUST NOT contain full diff text

### Requirement: Worktree-Backed Patch Apply Uses A Distinct Patch State

系统 SHALL mark a patch applied inside an isolated worktree as `applied_in_worktree`. This state indicates the patch was successfully applied in a retained worktree and MUST NOT imply the main working tree was modified.

Historical `applied` records MAY remain for older stages and MUST NOT be rewritten during V20 migration.

#### Scenario: Worktree-backed patch success uses isolated state

- **WHEN** a confirmed patch apply succeeds inside a V20 worktree
- **THEN** the patch store records `applied_in_worktree`
- **AND** the public answer MUST NOT state that the main working tree was changed

### Requirement: Worktree Disposal Uses Scoped Patch Terminal Updates

系统 SHALL provide a true no-create existing patch-store lookup and a scoped patch status update qualified by `patch_id + user_id + repo_key`.

V23 disposal/reconciliation MUST use the scoped update to transition an associated `applied_in_worktree` patch to `discarded` only after worktree cleanup and worktree metadata closeout succeed. The legacy unscoped `mark_status` method SHALL remain available for compatibility and MUST NOT be used by V23.

#### Scenario: Missing patch store is not created during preflight

- **WHEN** V23 checks a repo without an existing patch database
- **THEN** it returns a safe failure
- **AND** it MUST NOT create `.repopilot` or the patch database
