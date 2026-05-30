# harness-development-workflow Specification

## Purpose

记录 RepoPilot 仓库的阶段化开发、OpenSpec 规格入口、Harness 写入边界、验证和交接规则。
## Requirements
### Requirement: 仓库使用阶段化开发流程

仓库 SHALL 一次只开发一个小阶段，并且 MUST 保持阶段 scope 明确。

#### Scenario: 新阶段开始

- **WHEN** 新阶段开始
- **THEN** Agent 在修改文件前确认分支、工作区状态和当前阶段

### Requirement: allowed files 定义写入范围

仓库 SHALL 维护 `.harness/allowed_files.md` 作为当前阶段写入边界。

#### Scenario: 实现开始

- **WHEN** Agent 开始实现
- **THEN** 只编辑 `.harness/allowed_files.md` 允许的文件

### Requirement: review checklist 定义验收风险

仓库 SHALL 维护 `.harness/review_checklist.md` 作为当前阶段 review 标准。

#### Scenario: 进行 review

- **WHEN** 变更被 review
- **THEN** reviewer 检查 scope、允许文件、测试、文档、架构边界和 Roadmap 准确性

### Requirement: 验证使用确定性命令

仓库 SHALL 优先使用 `scripts/verify.ps1`、pytest 和 ruff 进行确定性验证。

#### Scenario: 变更完成

- **WHEN** 变更准备 review 或合并
- **THEN** 运行 `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`，或记录无法运行的原因

### Requirement: handoff 和 progress 保持最新

仓库 SHALL 在有意义的工作结束时更新 `docs/PROGRESS.md` 和 `HANDOFF_TO_NEXT_CHAT.md`。

#### Scenario: 工作 session 结束

- **WHEN** 阶段状态变化或实现完成
- **THEN** progress 和 handoff 文档记录分支、完成内容、验证、未完成事项和下一步建议

### Requirement: OpenSpec 是项目级开发流程

仓库 SHALL 在规划重要新阶段时使用 OpenSpec 管理 proposal、design、tasks、specs 和 archive。

#### Scenario: 规划重要新阶段

- **WHEN** 新的重要阶段被规划
- **THEN** Agent 在实现前创建或更新 OpenSpec change

### Requirement: OpenSpec 不等于运行时能力

OpenSpec、Superpowers、MCP、plugin 和外部 skill 概念 MUST NOT 被视为 RepoPilot 运行时能力，除非阶段 spec 明确开放该 scope。

#### Scenario: 存在 OpenSpec 工作流

- **WHEN** 仓库存在 OpenSpec 文件或项目级 AI skills
- **THEN** 应用运行时行为不因此改变，除非专门的产品 spec 要求改变

### Requirement: OpenSpec specs 是长期规格入口

仓库 SHALL 使用 `openspec/specs/` 作为长期规格入口。旧 `specs/00x-*` 迁移完成后 MUST NOT 继续作为当前规格入口维护。

#### Scenario: Agent 查找长期规格

- **WHEN** Agent 需要查看当前已验收能力规格
- **THEN** Agent 读取 `openspec/specs/` 中的 capability specs

#### Scenario: 旧 specs 已退役

- **WHEN** Agent 看到历史迁移记录
- **THEN** Agent 将旧 `specs/00x-*` 视为已迁移来源，而不是当前可编辑规格入口

### Requirement: 后续阶段采用轻量工程化路线

项目 SHALL 优先通过清晰边界、结构化审计、确定性验证、可替换接口和交接文档体现工程化。项目 MUST NOT 为了“看起来工程化”而在无明确阶段需求时引入重型基础设施。

V14 Long Task SHALL 使用 repo-local SQLite、确定性模板、摘要级 ReAct trace 和现有权限/审批/ToolExecutor 边界。V14 MUST NOT 引入后台 worker、外部队列、真实 subagent runtime、worktree automation、Shell executor 或新的公开 task API。

#### Scenario: V14 轻量长任务阶段

- **WHEN** V14 实现 Long Task Control Plane
- **THEN** 系统使用 repo-local SQLite 和确定性模板作为默认实现
- **AND** 系统保持 `/chat` contract 和现有 Harness 边界
- **AND** review checklist MUST 检查 Long Task 指令路由优先级、repo_key 规范化、quota/archive、redaction 和 non-goals
