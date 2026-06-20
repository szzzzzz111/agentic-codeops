# 当前 Harness 写入边界

当前无 active product development stage。本轮是独立的 process-only workflow maintenance，
用于精简阶段规划、review、Stage Debt Sweep、archive、merge/push 与最终 handoff；不创建 V24，
不修改 RepoPilot runtime。

## 当前允许修改

- `.harness/allowed_files.md`
- `.harness/review_checklist.md`
- `.harness/rules.md`
- `.harness/templates/stage_planning.md`
- `.harness/templates/stage_closeout.md`
- `docs/AGENT_RULES.md`
- `docs/PROGRESS.md`
- `HANDOFF_TO_NEXT_CHAT.md`
- `openspec/specs/harness-development-workflow/spec.md`
- `scripts/check_skill_evals.ps1`
- `scripts/check_stage_docs.ps1`
- `scripts/check_stage_closeout.ps1`
- `.codex/skills/repo-stage-workflow/**`
- `.codex/skills/openspec-stage-planner/**`
- `.codex/skills/repo-stage-review-loop/**`
- `.codex/skills/repo-stage-handoff/**`

## 禁止修改 / 禁止行为

- 不把连续执行授权解释为跳过正式 review、Stage Debt Sweep、验证或 closeout gate。
- 不恢复旧 `specs/00x-*` 作为规格入口。
- 不把 OpenSpec、Superpowers、MCP、plugin 或 `.codex/skills/**` 写成 RepoPilot runtime 能力。
- 不新增 `/chat` 顶层字段或公开 API。
- 不修改 `app/**`、`tests/**`、`docs/FEATURE_LIST.json` 或 runtime capability specs。
- 不创建 V24 或其他产品功能 change。
- 不把动态 Git HEAD/remote hash 复制到多份 durable docs。
