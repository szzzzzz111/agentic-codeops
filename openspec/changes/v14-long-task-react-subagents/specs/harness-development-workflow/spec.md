# harness-development-workflow Specification

## MODIFIED Requirements

### Requirement: 后续阶段采用轻量工程化路线

项目 SHALL 优先通过清晰边界、结构化审计、确定性验证、可替换接口和交接文档体现工程化。项目 MUST NOT 为了“看起来工程化”而在无明确阶段需求时引入重型基础设施。

V14 Long Task SHALL 使用 repo-local SQLite、确定性模板、摘要级 ReAct trace 和现有权限/审批/ToolExecutor 边界。V14 MUST NOT 引入后台 worker、外部队列、真实 subagent runtime、worktree automation、Shell executor 或新的公开 task API。

#### Scenario: V14 轻量长任务阶段

- **WHEN** V14 实现 Long Task Control Plane
- **THEN** 系统使用 repo-local SQLite 和确定性模板作为默认实现
- **AND** 系统保持 `/chat` contract 和现有 Harness 边界
- **AND** review checklist MUST 检查 Long Task 指令路由优先级、repo_key 规范化、quota/archive、redaction 和 non-goals
