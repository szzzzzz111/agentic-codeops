# RepoPilot OpenSpec

本目录用于 RepoPilot 的项目级 OpenSpec / SDD 工作流。OpenSpec 只服务于本仓库开发流程，不是 RepoPilot 的运行时功能。

## 使用边界

- 使用 OpenSpec 组织 change、proposal、design、tasks、spec delta 和 archive。
- Codex 使用仓库内 `.codex/skills` 和本文档理解 OpenSpec 流程。
- 本仓库不安装、不要求 Codex 全局 prompts，例如 `C:\Users\...\ .codex\prompts`。
- OpenCode 使用仓库内 `.opencode`。
- GitHub Copilot 当前不通过仓库内 `.github` OpenSpec prompts/skills 维护；如需启用，必须单独建 change。
- 不因为 OpenSpec 接入而引入 MCP server、plugin runtime、skill 执行、动态工具注册或 `/chat` 决策变更。

## 常用命令

```powershell
openspec list
openspec list --specs
openspec new change "<change-name>"
openspec status --change "<change-name>"
openspec validate "<change-name>"
openspec archive "<change-name>"
```

OpenSpec CLI 会提示匿名 telemetry。需要临时关闭时可在当前 PowerShell 会话中运行：

```powershell
$env:OPENSPEC_TELEMETRY = "0"
```

## 与现有 Harness 的关系

- OpenSpec 管理“要做什么、为什么、验收标准和变更归档”。
- `.harness/allowed_files.md` 和 `.harness/review_checklist.md` 继续管理当前阶段允许修改范围和 review 纪律。
- `docs/PROGRESS.md` 和 `HANDOFF_TO_NEXT_CHAT.md` 继续记录长期进度和跨 session 交接。
- 旧 `specs/00x-*` 暂时保留，不在本阶段迁移；后续如迁移，必须单独建 OpenSpec change。
