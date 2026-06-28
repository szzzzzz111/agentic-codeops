## Why

RepoPilot 已经有一套可执行的 OpenSpec / Harness / review / handoff 流程，但本地
`repo-stage-workflow` skill 对外部 AI-native 工作流的可取部分表达得还不够明确：
OpenSpec 应承担需求、接口/模型、任务拆解、规格评审、需求变更与归档；Superpowers
类执行纪律应承担读规格、隔离开发、TDD、验证、review、finish 和技能级自检。

本 change 吸收这个分工，并把它写成仓库内开发流程文档。它不改变 RepoPilot runtime，
不让 OpenSpec、Superpowers、skills、MCP 或 plugin 成为产品运行时能力。

同时修正上个阶段 closeout 后遗留的两处 current-state 文档漂移：`docs/PROGRESS.md`
和 `HANDOFF_TO_NEXT_CHAT.md` 仍把已 merge/push 的 repo mutation locking 写成待收尾。

## What Changes

- 更新 `.codex/skills/repo-stage-workflow/SKILL.md`：
  - 明确 OpenSpec owns specification baseline。
  - 明确 Superpowers owns execution discipline。
  - 明确需求变化或实现暴露设计矛盾时先回 OpenSpec，再回执行计划。
  - 明确 final docs sync 只更新拥有事实变化的文档，避免复制 volatile Git 状态。
- 更新 `harness-development-workflow` spec，记录 workflow skill 应保持规格基线与执行纪律分工。
- 同步 `.harness/allowed_files.md` 和 `.harness/review_checklist.md`。
- 修正 `docs/PROGRESS.md` 与 `HANDOFF_TO_NEXT_CHAT.md` 的 post-merge/push 漂移。

## Capabilities

### New Capabilities

- None. This is development process documentation only.

### Modified Capabilities

- `harness-development-workflow`: clarify the OpenSpec / execution-discipline split for repo-local workflow skills.

## Impact

- OpenSpec planning files:
  `openspec/changes/update-repo-stage-workflow-skill/**`.
- Harness files:
  `.harness/allowed_files.md`, `.harness/review_checklist.md`.
- Workflow skill:
  `.codex/skills/repo-stage-workflow/SKILL.md`.
- Drift corrections:
  `docs/PROGRESS.md`, `HANDOFF_TO_NEXT_CHAT.md`.
- Test assertion:
  `tests/test_chat_api.py` docs consistency assertion only.
- Out of scope:
  `app/**`, tests outside the docs consistency assertion, public `/chat` contract, provider runtime, live eval, default CI,
  network dependencies, commit/merge/push automation, branch/PR automation, background tasks,
  runtime subagents, connectors, notifications, and any RepoPilot runtime skill execution.
