# 当前 Harness 写入边界

Active OpenSpec change：无。

当前没有阶段级写入白名单。启动新阶段前，必须先按 `AGENTS.md` 和 repo-local
`repo-stage-workflow` 刷新仓库状态，创建或选择 OpenSpec change，并重新同步本文件与
`.harness/review_checklist.md`。

最近完成阶段：`derive-capability-status-from-runtime`，已归档到
`openspec/changes/archive/2026-07-06-derive-capability-status-from-runtime/`。

## 默认边界

- 未进入新阶段前，不应修改 runtime、tests、specs、docs 或 workflow 文件。
- 新阶段必须先明确 scope、risk、allowed paths、non-goals 和 required evidence。
- 不把 OpenSpec、Codex/OpenCode skills、Superpowers、MCP、plugin 或 descriptor-only 概念写成
  RepoPilot runtime 能力。
- 不实现 MCP server、MCP tool discovery、动态工具注册、Skill execution、connector、
  runtime subagent、background worker、notifications、always-on assistant、commit/merge/push
  automation 或 branch/PR automation，除非新的 OpenSpec change 明确批准。
