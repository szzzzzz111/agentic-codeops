# 评审清单：V4 Skill Loader 计划阶段

- [ ] 当前分支是 `feature/v4-skill-loader`。
- [ ] 只修改了 V4 计划阶段允许文件。
- [ ] 未修改 `app/` 运行时代码。
- [ ] 未修改 `tests/` 测试代码。
- [ ] 已创建 `specs/004-skill-loader/spec.md`、`plan.md`、`tasks.md`。
- [ ] V4 specs 明确只做 DeepAgents 风格 Skill Metadata Loader。
- [ ] V4 specs 明确只发现 `.agents/skills/*/SKILL.md` 的 `name`、`description`、`path`。
- [ ] V4 specs 明确不执行 skill、不读取完整 skill 正文、不做 progressive disclosure、不接入 `/chat` 决策。
- [ ] V4 specs 明确不接真实 LLM、不做 RAG、Memory、Reflection、eval 或复杂多 Agent。
- [ ] V4 specs 明确后续 progressive disclosure 和 skill-aware agent loop 是后续阶段。
- [ ] 没有把 Skill Loader、trace audit、PermissionPolicy、ApprovalGate、SandboxRunner、Reflection、eval、RAG 或 Memory 写成已实现。
- [ ] 已更新 `docs/PROGRESS.md` 或 `HANDOFF_TO_NEXT_CHAT.md` 中必要的交接说明。
- [ ] 已运行 `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`，或说明无法运行的原因。
