# 当前 Review 清单

当前阶段：V5 Skill Content Loader / progressive disclosure。

基础检查项：

- [ ] 当前变更对应 OpenSpec change：`v5-skill-content-loader`。
- [ ] `.harness/allowed_files.md` 已更新为当前阶段写入边界。
- [ ] 修改文件没有超出 `.harness/allowed_files.md`。
- [ ] 变更没有恢复旧 `specs/00x-*` 作为规格入口。
- [ ] OpenSpec、Superpowers、MCP、plugin 或外部 skill 没有被误写成 RepoPilot runtime 能力。

V5 范围检查项：

- [ ] V5 只增加按需读取完整 `SKILL.md` 的 loader 能力。
- [ ] `load_skill_metadata(repo_path)` 仍只返回 `name`、`description` 和相对 `path`，不返回完整正文。
- [ ] Content Loader 只允许读取 `.agents/skills/<skill>/SKILL.md`。
- [ ] Content Loader 返回结构与 spec 一致：`{"path": "...", "content": "..."}`。
- [ ] Content Loader 只做完整文件读取，不解析 frontmatter，不验证 `name` / `description`。
- [ ] Content Loader 拒绝路径逃逸、非 skill 文件、缺失文件和符号链接目录绕过。
- [ ] Content Loader 有明确读取规模上限，超限 fail fast。
- [ ] 返回路径不泄露本机绝对路径。
- [ ] 未接入 `/chat`、`CodeAgent` 或 `ToolExecutor` 决策。
- [ ] 未执行 skill，未接真实 LLM，未自动把 skill 内容注入 prompt。
- [ ] 未把 RAG、Memory、Reflection、PermissionPolicy、ApprovalGate、SandboxRunner 或 eval 写成已实现。

验证检查项：

- [ ] 已运行 `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`，或说明无法运行的原因。
- [ ] 已运行 `openspec validate v5-skill-content-loader`，或说明无法运行的原因。
- [ ] 提交前已检查 `git status --short --branch`、`git diff --name-only` 和 `git diff --check`。
