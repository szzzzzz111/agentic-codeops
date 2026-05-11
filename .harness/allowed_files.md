# OpenSpec 项目级工作流接入允许文件

- `openspec/README.md`
- `openspec/changes/README.md`
- `openspec/changes/archive/README.md`
- `openspec/specs/README.md`
- `.codex/skills/**`
- `.opencode/**`
- `.harness/allowed_files.md`
- `.harness/review_checklist.md`
- `.harness/rules.md`
- `AGENTS.md`
- `docs/AGENT_RULES.md`
- `docs/PROGRESS.md`
- `HANDOFF_TO_NEXT_CHAT.md`

本阶段只允许接入项目级 OpenSpec 工作流和项目内 Codex/OpenCode 提示，不开放 `app/` 运行时代码、`tests/` 测试代码或 RepoPilot 产品能力修改。

OpenSpec 只作为本仓库开发流程使用，不是 RepoPilot runtime 功能。不得安装或要求 Codex 全局 prompts，不得把 OpenSpec、Superpowers、MCP、plugin 或外部 skill 写成产品运行时能力。
