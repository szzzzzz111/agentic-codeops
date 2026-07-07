# 当前 Review 清单

Active OpenSpec change：无。

当前没有 active stage review checklist。启动新阶段前，必须先按最新 RepoPilot 工作流重新创建
或同步 `.harness/allowed_files.md` 与本文件。

最近完成阶段：`derive-capability-status-from-runtime`。

- OpenSpec archive：`openspec/changes/archive/2026-07-06-derive-capability-status-from-runtime/`
- Risk：medium / L2 human review depth
- Result：capability-status（能力状态）和 Assistant Control Surface（助手控制面）的当前能力摘要
  已从 active `ToolRegistry` backing primitives（支撑运行时原语）和固定安全边界派生。
- Non-goals：未实现 MCP、Skill execution、connector、runtime subagent、background worker、
  durable execution、dynamic tool registration、public descriptor API、commit/push/branch/PR automation。
- Final review：internal review 和 OpenCode final review 的 blocking findings 均已关闭；
  Focused Stage Debt Sweep 未发现新增 blocking debt。
- Archive-after verification：`openspec list` 为 No active changes found；
  `openspec validate --all` 为 22 passed、0 failed；full `scripts/verify.ps1` 为
  pytest 525 passed、1 skipped，ruff、stage docs scan、skill eval structure scan passed；
  `git diff --check` passed，仅 CRLF normalization warnings。
