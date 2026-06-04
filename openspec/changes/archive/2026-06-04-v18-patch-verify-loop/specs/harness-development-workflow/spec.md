## MODIFIED Requirements

### Requirement: 后续阶段采用轻量工程化路线

项目 SHALL 优先通过清晰边界、结构化审计、确定性验证、可替换接口和交接文档体现工程化。项目 MUST NOT 为了“看起来工程化”而在无明确阶段需求时引入重型基础设施。

V18 Patch + Verify Loop SHALL 使用现有 `/chat` 入口、明确组合确认、pending patch apply、白名单验证命令、权限审批边界和受控 `patch_apply` / `verification_run` 工具串联一次 apply 后 verify。V18 MUST NOT 新增公开 API、新增 `/chat` 顶层字段、开放任意 shell、支持用户自定义验证参数、根据失败自动生成 patch、持久化验证结果、自动 commit、创建 worktree、调度真实 subagents、执行后台任务或实现 Persistent Audit / Recovery。

#### Scenario: V18 受控 Patch + Verify Loop 阶段

- **WHEN** V18 实现 Patch + Verify Loop
- **THEN** 系统通过 `/chat.answer` 返回组合结果摘要
- **AND** 系统保持 `/chat` contract 和现有 Harness 权限边界
- **AND** review checklist MUST 检查组合确认优先级、半解析拒绝、命令白名单、独立 verification context、失败门、输出脱敏、contract 和 non-goals
