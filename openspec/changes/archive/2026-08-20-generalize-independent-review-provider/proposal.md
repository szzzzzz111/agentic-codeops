## Why

RepoPilot 当前把 medium/high 阶段的两个独立计划评审席位写死为 Codex 和 OpenCode，导致评审门禁依赖某个 Agent 品牌是否可用，而没有直接约束真正需要的上下文隔离、审阅对象冻结和独立反例输出。现在需要允许 OpenCode 席位由另一个 Codex 实例替代，同时避免同一实现上下文内的自审被误算成独立评审。

## What Changes

- 保留 medium/high 阶段现有的 internal review 加两个 independent review slots，不减少评审数量。
- 将 OpenCode 从强制 reviewer 改成可选 reviewer adapter；每个独立席位可由 OpenCode 或 Codex 等受支持的工程 Agent 实例承担。
- 要求 Codex 首轮独立评审使用空上下文任务，或使用明确不继承父对话的子智能体；继承实现上下文的实例不能满足独立评审门禁。
- 要求两个首轮独立 reviewer 互相不可见对方结论，并只接收冻结的 plan 或 final implementation review packet。
- 允许修复后的 re-review 复用原 reviewer 会话，以保持 finding 身份和关闭链路；复用不等于首轮可继承实现上下文。
- 要求修复后每个 required slot 的最终结论都绑定同一份最终 content-addressed baseline；旧 baseline 的 no-findings 不得继续计数。
- 将 reviewer 类型、implementer/reviewer 实例标识、上下文模式、不可变被审 ref/hash、最终 findings/no-findings、closure 状态和 residual uncertainty 纳入固定 receipt，并用确定性 validator 拒绝可机械识别的矛盾；宿主 dispatch 来源与 activation 时序仍由仓库外控制器/变更前流程 authority 验证，不伪装成 repository validator 能证明的事实。
- 更新结构测试，检查独立性合同而不是硬编码 `OpenCode independent plan review` 字样。
- 定义一次性 activation boundary：本 change 的 plan review 由变更前合同和冻结 hashes 留证；新 validator 实现并通过负样本后才激活，不追溯制造 pre-implementation machine PASS。

## Capabilities

### New Capabilities

无。这是开发流程调整，不新增 RepoPilot runtime capability。

### Modified Capabilities

- `harness-development-workflow`: 将固定 Codex/OpenCode 评审组合改为 provider-neutral 的独立评审席位合同，并定义 Codex 替代、首轮上下文隔离、re-review 复用和证据要求。

## Impact

- Workflow/spec：`openspec/specs/harness-development-workflow/spec.md`、`docs/AGENT_RULES.md`、`.harness/rules.md`。
- Codex skills：`openspec-stage-planner`、`repo-stage-workflow`、`repo-stage-review-loop` 及 `workflow-contract` reference。
- OpenCode adapter：`.opencode/skills/openspec-plan-review/SKILL.md` 区分首轮隔离与同一席位的修复复审。
- Deterministic process evidence：`.harness/templates/independent-review-receipt.template.json`、`scripts/validate_independent_review.py` 及其负样本测试。
- Stage review evidence：`.harness/reviews/<stage-id>/<phase>/review-set.json`；required independent slots 只有在实际 receipt set 通过机械一致性 validator，且宿主 dispatch provenance 与 activation sequence 的外部门禁都完成后才能计数。
- Migration evidence：`openspec/changes/generalize-independent-review-provider/plan-review.md` 记录本 change 在旧合同下完成的 hash-bound manual plan review；它不是新 validator 的 PASS receipt。
- Tests：`tests/test_cli.py` 的 workflow skill 结构断言和 `tests/test_independent_review_validation.py`。
- Stage evidence：`.harness/allowed_files.md`、`.harness/review_checklist.md`、`docs/PROGRESS.md`、`HANDOFF_TO_NEXT_CHAT.md`。
- 不修改 `app/**`、公开 `/chat` contract、runtime provider/subagent 行为、默认 CI 或网络依赖；不执行 merge/push。
