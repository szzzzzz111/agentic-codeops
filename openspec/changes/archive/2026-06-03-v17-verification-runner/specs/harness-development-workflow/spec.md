## MODIFIED Requirements

### Requirement: 后续阶段采用轻量工程化路线

项目 SHALL 优先通过清晰边界、结构化审计、确定性验证、可替换接口和交接文档体现工程化。项目 MUST NOT 为了“看起来工程化”而在无明确阶段需求时引入重型基础设施。

V17 Verification Runner SHALL 使用现有 `/chat` 入口、明确验证请求、白名单验证命令、权限审批边界和受控 `verification_run` 工具执行 `pytest`、`ruff check .` 或 `scripts/verify.ps1`。V17 MUST NOT 新增公开 API、新增 `/chat` 顶层字段、开放任意 shell、自动在 patch apply 后运行验证、根据失败自动生成 patch、持久化验证结果、自动 commit、创建 worktree、调度真实 subagents、执行后台任务或实现 Patch + Verify Loop。

#### Scenario: V17 受控验证阶段

- **WHEN** V17 实现 Verification Runner
- **THEN** 系统通过 `/chat.answer` 返回验证结果摘要
- **AND** 系统保持 `/chat` contract 和现有 Harness 权限边界
- **AND** review checklist MUST 检查验证 intent、命令白名单、权限上下文、ToolExecutor 执行、输出脱敏、contract 和 non-goals
