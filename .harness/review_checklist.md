# 评审清单：V4 Skill Metadata Loader 实现阶段

- [ ] 当前分支是 `feature/v4-skill-loader`。
- [ ] 只修改了 V4 实现阶段允许文件。
- [ ] 未修改 API handler、Service 层、Agent loop 或既有 file tools 行为。
- [ ] 已创建 `specs/004-skill-loader/spec.md`、`plan.md`、`tasks.md`。
- [ ] V4 specs 明确只做 DeepAgents 风格 Skill Metadata Loader。
- [ ] V4 specs 明确只发现 `.agents/skills/*/SKILL.md` 的 `name`、`description`、`path`。
- [ ] V4 specs 明确不执行 skill、不读取完整 skill 正文、不做 progressive disclosure、不接入 `/chat` 决策。
- [ ] V4 specs 明确不接真实 LLM、不做 RAG、Memory、Reflection、eval 或复杂多 Agent。
- [ ] V4 specs 明确后续 progressive disclosure 和 skill-aware agent loop 是后续阶段。
- [ ] 已实现独立 Skill Metadata Loader，不把技能逻辑堆到 API、Service 或 Agent 层。
- [ ] Loader 只读取 `SKILL.md` frontmatter 的 `name` 和 `description`。
- [ ] Loader 返回相对仓库路径，不返回本机绝对路径。
- [ ] 没有返回完整 skill 正文，也没有把 skill 正文注入 prompt。
- [ ] 没有改变 `/chat` 请求和响应行为。
- [ ] 已增加 metadata 命中、无 skills 目录、多技能稳定排序、不返回完整正文和不泄露本机绝对路径测试。
- [ ] 没有把 Skill Loader、trace audit、PermissionPolicy、ApprovalGate、SandboxRunner、Reflection、eval、RAG 或 Memory 写成已实现。
- [ ] 已更新 `docs/PROGRESS.md` 或 `HANDOFF_TO_NEXT_CHAT.md` 中必要的交接说明。
- [ ] 已运行 `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`，或说明无法运行的原因。
