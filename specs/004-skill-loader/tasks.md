# 任务：V4 Skill Metadata Loader

## 计划阶段

- [x] 确认当前分支是 `feature/v4-skill-loader`。
- [x] 确认 `.harness/allowed_files.md` 已切换到 V4 计划阶段。
- [x] 确认 `.harness/review_checklist.md` 已切换到 V4 计划阶段。
- [x] 创建 `specs/004-skill-loader/spec.md`。
- [x] 创建 `specs/004-skill-loader/plan.md`。
- [x] 创建 `specs/004-skill-loader/tasks.md`。
- [x] 明确 V4 只做 DeepAgents 风格 Skill Metadata Loader。
- [x] 明确 V4 只发现 `.agents/skills/*/SKILL.md` 的 `name`、`description`、`path`。
- [x] 明确 V4 不执行 skill。
- [x] 明确 V4 不读取完整 skill 正文。
- [x] 明确 V4 不做 progressive disclosure。
- [x] 明确 V4 不接入 `/chat` 决策。
- [x] 明确 V4 不接真实 LLM、RAG、Memory、Reflection、eval 或复杂多 Agent。
- [x] 更新 `docs/PROGRESS.md`，记录 V4 specs 已创建。
- [x] 更新 `HANDOFF_TO_NEXT_CHAT.md`，交接 V4 specs 状态。
- [x] 运行 `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`。

## 后续实现阶段

- [x] 更新 `.harness/allowed_files.md`，开放 V4 实现需要的运行时代码和测试文件。
- [x] 更新 `.harness/review_checklist.md`，切换到 V4 实现阶段评审清单。
- [x] 新增 Skill Metadata Loader 模块。
- [x] 实现 `.agents/skills/*/SKILL.md` 发现。
- [x] 实现 `name` 和 `description` frontmatter 解析。
- [x] 返回相对仓库路径 `path`。
- [x] 保持不存在 skills 目录时返回空列表。
- [x] 保持多个技能返回顺序稳定。
- [x] 增加 metadata 命中测试。
- [x] 增加无 skills 目录测试。
- [x] 增加多技能稳定排序测试。
- [x] 增加不返回完整正文测试。
- [x] 增加不泄露本机绝对路径测试。
- [x] 增加非法 frontmatter 行 fail fast 测试。
- [x] 增加异常 frontmatter 读取限制测试。
- [x] 确认 `/chat` 行为不变。
- [x] 更新 README、`docs/PROGRESS.md` 和 `HANDOFF_TO_NEXT_CHAT.md`。
- [x] 必要时更新 `docs/FEATURE_LIST.json`。

## 验证

- [x] 运行 `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`。
- [x] 确认 `pytest` 通过。
- [x] 确认 `ruff check .` 通过。

## 延后

- [ ] Skill 正文按需读取。
- [ ] Progressive disclosure。
- [ ] Skill-aware Agent Loop。
- [ ] 真实 LLM 接入。
- [ ] 自动修改代码。
- [ ] shell 工具。
- [ ] 多 Agent。
- [ ] RAG。
- [ ] Memory。
- [ ] Reflection。
- [ ] eval。
- [ ] PermissionPolicy。
- [ ] ApprovalGate。
- [ ] SandboxRunner。
