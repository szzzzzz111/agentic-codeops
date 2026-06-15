# 当前 Harness 写入边界

当前无 active development stage。V23 merge 后 review findings 已完成 remediation、正式 re-review
与 full verification。

开始下一阶段前，必须创建对应 OpenSpec change，并重新同步本文件与
`.harness/review_checklist.md`。

## 当前允许修改

- V23 remediation merge durable docs、handoff closeout 与 review-process hardening 文件。
- 允许更新 `docs/AGENT_RULES.md`、`.harness/rules.md`、`.harness/review_checklist.md`、
  `openspec/specs/harness-development-workflow/spec.md`、`docs/PROGRESS.md` 与
  `HANDOFF_TO_NEXT_CHAT.md`，用于沉淀最终 review / Stage Debt Sweep 结论。

## 禁止修改 / 禁止行为

- 不把连续执行授权解释为跳过正式 review、Stage Debt Sweep、验证或 closeout gate。
- 不恢复旧 `specs/00x-*` 作为规格入口。
- 不把 OpenSpec、Superpowers、MCP、plugin 或 `.codex/skills/**` 写成 RepoPilot runtime 能力。
- 不新增 `/chat` 顶层字段或公开 API。
