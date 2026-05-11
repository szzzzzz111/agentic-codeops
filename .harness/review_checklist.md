# 评审清单：OpenSpec 项目级工作流接入

- [ ] 当前分支是 `feature/openspec-workflow`。
- [ ] 只修改了 OpenSpec 项目级工作流接入允许文件。
- [ ] 未修改 `app/` 运行时代码。
- [ ] 未修改 `tests/` 测试代码。
- [ ] 已保留项目内 `.codex/skills`，但没有安装或要求 Codex 全局 prompts。
- [ ] 已生成项目内 `.opencode` OpenSpec 提示文件。
- [ ] 未保留 `.github` OpenSpec 提示文件，因为 Copilot 已通过 OpenSpec 其他方式对接。
- [ ] 已新增可被 Git 跟踪的 `openspec/` README 文件，避免只有空目录。
- [ ] `AGENTS.md` 明确 OpenSpec 是本仓库项目级 SDD 流程，不是 RepoPilot runtime 功能。
- [ ] `.harness/rules.md` 明确不得把 OpenSpec、Superpowers、MCP、plugin 或外部 skill 写成产品运行时能力。
- [ ] 未引入 MCP server、plugin runtime、skill 执行或 `/chat` 决策变更。
- [ ] 已运行 `openspec list` 和 `openspec list --specs`，确认 CLI 可在项目内执行。
- [ ] 已运行 `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`，或说明无法运行的原因。
- [ ] 已运行 `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`，或说明无法运行的原因。
