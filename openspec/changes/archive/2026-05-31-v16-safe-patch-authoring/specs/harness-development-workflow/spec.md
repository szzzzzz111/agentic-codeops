# harness-development-workflow Specification

## MODIFIED Requirements

### Requirement: 后续阶段采用轻量工程化路线

项目 SHALL 优先通过清晰边界、结构化审计、确定性验证、可替换接口和交接文档体现工程化。项目 MUST NOT 为了“看起来工程化”而在无明确阶段需求时引入重型基础设施。

V16 Safe Patch Authoring SHALL 使用现有 `/chat` 入口、repo evidence、pending patch store、明确确认语法和受控 `patch_apply` 写入工具。V16 MUST NOT 新增公开 API、新增 `/chat` 顶层字段、执行 shell、运行验证命令、自动 commit、创建 worktree、调度真实 subagents、执行后台任务或实现 Patch + Verify Loop。

#### Scenario: V16 安全 patch 阶段

- **WHEN** V16 实现 Safe Patch Authoring
- **THEN** 系统通过 `/chat.answer` 返回 patch proposal 或 apply 结果
- **AND** 系统保持 `/chat` contract 和现有 Harness 权限边界
- **AND** review checklist MUST 检查路由优先级、provider schema、pending store、确认语法、权限上下文、安全写入、redaction、contract 和 non-goals
