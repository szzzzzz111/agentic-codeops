## Context

RepoPilot 的 medium/high 阶段当前要求 internal、Codex independent 和 OpenCode independent 三层计划评审。这个数量和独立反例目标应保留，但 `OpenCode` 被写成了不可替换的门禁；当 OpenCode 不可用时，流程只能请求降级，即使 Codex 能通过新的空上下文任务或不继承父对话的子智能体提供真正独立的审阅。

本阶段只调整开发流程。这里的 Codex task/subagent 是开发环境中的 reviewer execution form，不是 RepoPilot runtime 的 subagent capability。当前 OpenCode 专用 skill 和会话复审方式仍然有用，应作为 adapter-specific guidance 保留。

## Goals / Non-Goals

**Goals:**

- 保留 medium/high plan review 的 internal review 加两个独立评审席位；final implementation review 的 required slot 数量继续由现有风险合同决定。
- 让 reviewer provider 可替换，同时对上下文隔离、被审版本、输出和身份留证提出可验证要求。
- 允许 Codex 空上下文任务或显式关闭父上下文继承的子智能体替代 OpenCode 席位。
- 区分首轮 blind review（盲审）与 remediation re-review（修复复审）：前者需要隔离，后者允许沿用原会话关闭原 finding。
- 让结构测试验证合同语义，而不是验证固定品牌字符串。

**Non-Goals:**

- 不减少 medium/high 阶段的独立评审席位数量。
- 不宣称同一模型的两个实例提供模型多样性；只证明实例与上下文独立，并记录 residual correlation risk。
- 不允许当前实现 Agent 在同一上下文里切换角色完成独立评审。
- 不新增 runtime subagent、provider、connector、MCP、后台执行或公开 API。
- 不删除 OpenCode adapter skill，不重写 archived change 和历史 review 事实。

## Decisions

### Decision 1: Bind the gate to review slots, not providers

Medium/high plan review 继续要求一个 internal review 和两个 independent review slots。每个独立席位由一个不同于 implementer、也不同于另一席位的 reviewer instance 承担；OpenCode、Codex 或其他受支持的工程 Agent 只是执行该席位的 adapter。Final implementation review 不新增固定的“两席位”要求，其 required slot 数量继续由 `low/medium/high` 风险合同决定，但每一个 required independent slot 都服从同一隔离合同。

Alternative considered: 只要求一个独立 reviewer。拒绝，因为这会借“工具替换”降低现有的两个独立席位强度。

### Decision 2: Define first-round independence by context and inputs

首轮 reviewer 只能接收冻结的 plan artifacts 或 final implementation review packet、review checklist 和必要的仓库路径/ref。它不能继承实现对话，也不能在形成首轮结论前读取另一 reviewer 的输出。

Codex 替代席位必须使用新的空上下文任务，或使用显式关闭父上下文继承的子智能体；在当前 Codex multi-agent API 中对应 `fork_turns="none"`。默认继承全部上下文或无法证明继承模式的实例不满足门禁。

Alternative considered: 只要不同 task/agent id 就算独立。拒绝，因为不同 id 仍可能继承相同实现推理和结论，无法阻止角色切换式自审。

### Decision 3: Re-review may preserve reviewer continuity

首轮 findings 被修复后，允许复用产生该 finding 的 reviewer 会话，检查既有 finding 的关闭和新 diff 是否引入同 scope 问题。这个实例仍只占原席位，不能同时充当第二个独立席位。任何 required slot 只有在其最终 receipt 绑定同一个最终 content-addressed baseline 时才能计数；未产生 finding 的另一席位也必须刷新到修复后的最终 baseline。

Alternative considered: 每轮都强制空上下文。拒绝，因为会丢失 finding lineage，并鼓励用新 reviewer 遗忘旧 blocker。

### Decision 4: Evidence records independence and residual uncertainty

每个独立评审席位使用固定 JSON receipt，记录 stage/phase/slot id、implementer identity、reviewer provider/model/instance id、host-reported context inheritance、首轮是否看过其他 reviewer 输出、不可变 Git/tree 或 packet-manifest ref/hash、reviewed artifact hashes、final findings 或 explicit no-findings、finding disposition/closure、residual uncertainty，以及 remediation lineage。Remediation receipt 还必须通过 `review_history` 引用并哈希绑定原始 first-round receipt，验证原 slot、reviewer 和 finding IDs。

`scripts/validate_independent_review.py` 对一个 frozen review set 做确定性检查：required slot 数量、slot/reviewer 唯一性、声明的 reviewer/implementer 分离与 context mode、cross-review visibility、共同 final baseline、canonical project-relative path、artifact hash、原 receipt-bound remediation lineage 和无矛盾/已关闭的 final conclusion。

Validator 的 claim ceiling 固定为 `mechanical_consistency_only`，输出 `gate_ready=false`，并列出 `HOST_DISPATCH_PROVENANCE` 与 `ACTIVATION_SEQUENCE` 两个 required external checks。仓库内 JSON 无法证明自身字段确实来自宿主 API，也无法证明 activation 的真实时间顺序；宿主控制器必须直接核对 task/subagent dispatch metadata，变更前流程 authority 必须核对 activation sequence。Validator 零退出只是必要条件，不是独立评审 gate 的充分条件。

每个阶段把实际 receipt set 存在 `.harness/reviews/<stage-id>/<phase>/review-set.json`，其中 `<phase>` 为 `plan` 或 `implementation`。命令接口固定为：

```text
python scripts/validate_independent_review.py \
  --project-root . \
  --receipt-set .harness/reviews/<stage-id>/<phase>/review-set.json \
  --expected-stage <stage-id> \
  --expected-phase <plan|implementation> \
  --required-slots <risk-contract-count>
```

receipt set 顶层包含 implementer identity、baseline artifact manifest、activation authority record hash、可选的原始 `review_history` 和各 slot 的最终 receipt。Validator 从项目根目录重算每个 reviewed artifact 的 SHA-256，再计算排序后的 content-addressed packet hash；所有 slot 必须引用该 hash。`--required-slots` 由当前风险合同/阶段 checklist 给出：medium/high plan 为 `2`，low-risk plan 为 `0` 或 checklist 明确要求的数量，final review 由风险合同决定，本 low-risk 阶段因用户额外要求 plan/final 各为 `1`。

Validator 向 stdout 输出 `repopilot.independent_review_validation/v1` JSON；所有错误列在 `errors`，任一错误或 receipt 缺失均退出非零。即使机械检查 PASS，输出也不会宣称 `gate_ready`；Workflow、planner、review-loop 和 checklist 必须运行并消费这个实际命令，再消费宿主/activation external checks。只存在 validator、只跑 unit tests、只勾 checklist 或只自填 `host_tool_metadata` 字样都不能让席位计数。

Alternative considered: 只保存 final text。拒绝，因为无法区分真正独立 reviewer 与同上下文自审。

### Decision 5: Keep adapter-specific recovery rules behind the generic contract

通用 workflow/spec/skills 表达独立评审席位合同。OpenCode 首轮使用新的隔离 review session；`session list` 和 session reuse 仅用于同一席位的 remediation re-review 或 timeout 后取回同一次 review 的 final assistant text。Codex skill 说明空任务或 `fork_turns="none"`。适配器故障只影响该实例；控制器必须换用另一个独立实例，不能因此减少 required slot 数量。

### Decision 6: Activate the new validator without retroactive evidence

本 change 的 pre-implementation plan review 使用仓库变更前的 manual review contract：空上下文 reviewer、冻结 planning packet hashes、findings/dispositions 和 same-slot remediation lineage 写入 active change 的 `plan-review.md`。因为 validator 是本 change 的实现产物，它不能成为允许自身实现开始的前置条件，也不能在实现后把 plan review 倒填成 machine-validated PASS。

新 gate 的 activation timing 仍由变更前 manual process authority 决定，并通过项目内 activation record path/hash 固定其声明；validator 只核对该 record 的完整性，不证明时序。Authority 在 receipt template、validator、负样本、workflow wiring 和 focused verification 全部完成后激活新 gate。激活后，本阶段 final implementation review 必须使用实际 receipt set、通过机械 validator 并通过两项 external checks；所有后续阶段的 required plan/final independent review 也必须使用它。

Alternative considered: 把 validator 拆成独立 bootstrap change。拒绝，因为本次 low-risk process change 可以用明确的一次性 migration boundary 保持真实时序，无需额外分支；若实现范围扩大或旧合同不足，则应改用拆分方案。

## Risks / Trade-offs

- [两个 Codex 实例仍有 correlated model risk] → 证据记录 provider/model，评审摘要保留 residual uncertainty；有可用异构 reviewer 时优先使用，但不把品牌可用性变成硬门禁。
- [“空上下文”无法由仓库单独观察] → repository validator 只检查声明结构并固定 `mechanical_consistency_only`/`gate_ready=false`；宿主控制器直接核对 native dispatch metadata。unknown 或只有仓库自填字段而没有宿主核对时 gate 保持打开，并保留无法证明模型认知独立性的 residual uncertainty。
- [首轮盲审妨碍 reviewer 理解必要背景] → 允许冻结 packet 包含 proposal/design/tasks/spec、diff、测试和边界，但不包含实现 Agent 的未冻结推理或其他 reviewer 结论。
- [re-review 被误算为新独立席位] → 规则明确 reused reviewer 只能关闭原席位 findings，不能增加独立席位计数；`review_history` 的原始 receipt/hash 必须解析到同 slot/reviewer/finding IDs。
- [validator 存在但从未被 review gate 消费] → skills/rules/checklist 固定实际 receipt-set command 和两项 external checks；缺失调用、非零退出或外部核对缺失都保持 gate open。
- [新 gate 要求在自身实现前先存在] → 本 change 的 plan review 使用 hash-bound 旧合同并留 migration record；变更前 authority 拥有 activation 时序，validator 只验证 record hash；新 gate 从本阶段 final review 起激活，禁止追溯声称 plan machine PASS。
- [开发 subagent 被误写成 runtime capability] → 所有流程文件保留 process-only non-goal，runtime docs/spec 不新增能力声明。

## Migration Plan

1. 先修改结构测试，使旧的 provider-hardcoded workflow 在新独立性断言下失败。
2. 更新 workflow spec、rules、Codex skills 和 OpenCode adapter，使用相同的 review-slot、fresh-context、final-baseline 和 re-review 语义。
3. 新增 receipt template、deterministic validator、workflow/review-loop eval 和正/负样本测试。
4. 记录本 change 的 hash-bound manual plan review 和 activation boundary；不得生成追溯性的 plan validator PASS。
5. 确认历史 docs/archive 不被重写。
6. 运行 focused tests、OpenSpec strict/all validation、可用的 stage/skill scans 和 full verification。
7. 激活 validator，按本 low-risk 阶段的用户要求用一个空上下文 Codex reviewer 对最终 diff 做独立复审，并验证实际 final receipt set；本阶段不 merge/push。

Rollback 可恢复原 workflow/spec/skill/test 文本；本阶段没有 runtime 或持久数据迁移。

## Open Questions

无。用户已明确允许 OpenCode 由空上下文 Codex 对话或子智能体替代；本设计保留 medium/high plan review 的现有评审数量，并把相同独立性要求应用于风险合同所要求的每一个 final implementation review slot。
