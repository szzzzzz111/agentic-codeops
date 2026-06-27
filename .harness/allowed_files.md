# 当前 Harness 写入边界

当前 active OpenSpec change：无。

V25 `add-verified-patch-promotion` 已归档到
`openspec/changes/archive/2026-06-27-add-verified-patch-promotion/`；当前没有开放的新阶段写入范围。

## 下一阶段开始前

- 先读取 `AGENTS.md` 及必读文档。
- 先检查分支、工作树、最近提交、远端同步状态和 `openspec list`。
- 新阶段必须先创建或选择 OpenSpec change，并同步本文件与 `.harness/review_checklist.md`。
- 未同步新阶段边界前，不默认开放 `app/**`、`tests/**`、`docs/**` 或 `openspec/specs/**` 的语义修改。

## 长期禁止行为

- 不修改 `/chat` public contract、默认 CI、provider runtime 或 live eval profile，除非新阶段 OpenSpec 明确批准。
- 不新增网络依赖，不要求 provider API key，不运行 live gate。
- 不实现 commit/merge/push automation、branch/PR automation、后台任务、runtime subagents、connectors、notifications 或 always-on assistant，除非新阶段明确批准。
- 不执行 `git worktree prune`。
- 不打印、提交或持久化 API key、完整 URL、prompt、EvidencePack、原始回答、完整 diff、patch body、raw exception、traceback、reasoning content、原始 fingerprint、HTTP payload、本机绝对路径、`.git` 路径或 DB 路径。
- 不把 OpenSpec、Codex/OpenCode skills、Superpowers、MCP、plugin 写成 RepoPilot runtime 能力。
