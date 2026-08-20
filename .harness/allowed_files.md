# 当前 Harness 写入边界

Active OpenSpec change：`generalize-independent-review-provider`。

本阶段是 low-risk、process-only 的开发工作流调整：把 medium/high 阶段的独立评审门禁从
固定 Agent 品牌改成可验证的独立评审席位。OpenCode 继续作为可选适配器；Codex 只有在首轮
评审使用空上下文任务，或使用明确不继承父对话的子智能体时，才能替代相应评审席位。

## 本阶段允许修改

- `openspec/changes/generalize-independent-review-provider/**`
- `openspec/specs/harness-development-workflow/spec.md`
- `.harness/allowed_files.md`
- `.harness/review_checklist.md`
- `.harness/rules.md`
- `.harness/templates/independent-review-receipt.template.json`
- `.harness/reviews/generalize-independent-review-provider/**`
- `docs/AGENT_RULES.md`
- `.codex/skills/openspec-stage-planner/SKILL.md`
- `.codex/skills/repo-stage-workflow/SKILL.md`
- `.codex/skills/repo-stage-workflow/references/workflow-contract.md`
- `.codex/skills/repo-stage-workflow/references/evals.md`
- `.codex/skills/repo-stage-review-loop/SKILL.md`
- `.codex/skills/repo-stage-review-loop/references/evals.md`
- `.opencode/skills/openspec-plan-review/SKILL.md`
- `scripts/validate_independent_review.py`
- `tests/test_cli.py`
- `tests/test_independent_review_validation.py`
- `docs/PROGRESS.md`
- `HANDOFF_TO_NEXT_CHAT.md`

## 本阶段 Non-goals

- 不修改 `app/**` 或任何 RepoPilot runtime 行为。
- 不新增 runtime subagent、provider、network、MCP、connector、background worker 或 API 能力。
- 不降低 medium/high 阶段既有的内部评审与两个独立评审席位数量。
- 不把同一上下文内的自审、继承父对话的子智能体或只复述任务状态计为独立评审。
- 不修改已归档 change 的历史事实，不删除 OpenCode 适配器；首轮必须新建/证明隔离，只有同一席位的 remediation re-review 可以复用原会话。
- 不执行 merge、push 或当前 dirty storage-refactor worktree 的任何修改。

## 默认边界

- 仅修改上述白名单中的 process/spec/skill/test/docs 文件。
- 行为合同由 active OpenSpec change 冻结；发现 scope 或独立性语义变化时先回到 plan review。
- 不把 OpenSpec、Codex/OpenCode skills、Superpowers、MCP、plugin 或 descriptor-only 概念写成
  RepoPilot runtime 能力。
- 不实现 MCP server、MCP tool discovery、动态工具注册、Skill execution、connector、
  runtime subagent、background worker、notifications、always-on assistant、commit/merge/push
  automation 或 branch/PR automation，除非新的 OpenSpec change 明确批准。
