## 1. Harness 边界

- [x] 1.1 更新 `.harness/allowed_files.md`，只开放 V5 Skill Content Loader 相关实现、测试、OpenSpec change 和必要文档。
- [x] 1.2 更新 `.harness/review_checklist.md`，增加 V5 content loading 的路径安全、规模限制和非 `/chat` 接入检查项。

## 2. 测试先行

- [x] 2.1 在 `tests/test_skill_loader.py` 增加按相对路径读取完整 `SKILL.md` 的成功用例，并断言返回结构为 `{"path": "...", "content": "..."}`。
- [x] 2.2 增加 content loader 返回路径不泄露本机绝对路径的测试。
- [x] 2.3 增加拒绝路径逃逸、非 skill 文件、缺失 skill 文件和符号链接目录绕过的测试。
- [x] 2.4 增加内容读取规模上限测试。
- [x] 2.5 确认既有 metadata 测试仍证明 `load_skill_metadata(repo_path)` 不返回完整正文。

## 3. 实现

- [x] 3.1 在 `app/tools/skill_loader.py` 增加完整 skill 内容读取函数，输入为 `repo_path` 和 metadata 返回的相对 `path`，返回结构与 spec 保持一致。
- [x] 3.2 复用或补充 repo 内路径校验，确保只允许 `.agents/skills/<skill>/SKILL.md`。
- [x] 3.3 为完整内容读取增加明确字符上限，超限 fail fast。
- [x] 3.4 保持 `load_skill_metadata(repo_path)` 行为和返回字段不变。

## 4. 文档与验证

- [x] 4.1 更新 `docs/PROGRESS.md`，记录 V5 当前阶段状态和边界。
- [x] 4.2 更新 `docs/FEATURE_LIST.json`，增加 V5 可验收功能条目；实现完成并验证通过后将 `passes` 标记为 `true`。
- [x] 4.3 更新 `HANDOFF_TO_NEXT_CHAT.md`，记录当前分支、OpenSpec change、未完成任务和下一步。
- [x] 4.4 运行 `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`。
- [x] 4.5 运行 `openspec validate v5-skill-content-loader`。
- [x] 4.6 提交前检查 `git status --short --branch`、`git diff --name-only` 和 `git diff --check`。
