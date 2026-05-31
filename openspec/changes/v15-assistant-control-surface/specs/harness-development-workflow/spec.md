# harness-development-workflow Specification

## MODIFIED Requirements

### Requirement: 后续阶段采用轻量工程化路线

项目 SHALL 优先通过清晰边界、结构化审计、确定性验证、可替换接口和交接文档体现工程化。项目 MUST NOT 为了“看起来工程化”而在无明确阶段需求时引入重型基础设施。

V15 Assistant Control Surface SHALL 使用现有 `/chat` 入口、确定性触发词、只读本地状态摘要和现有响应字段。V15 MUST NOT 新增公开 API、新增 `/chat` 顶层字段、执行 shell、生成或应用 patch、运行验证命令、创建 worktree、调度真实 subagents、执行后台任务或隐式初始化本地状态 DB。

#### Scenario: V15 轻量控制面阶段

- **WHEN** V15 实现 Assistant Control Surface
- **THEN** 系统通过 `/chat.answer` 返回只读控制面状态
- **AND** 系统保持 `/chat` contract 和现有 Harness 边界
- **AND** review checklist MUST 检查路由优先级、只读状态聚合、DB 非初始化、redaction、contract 和 non-goals
