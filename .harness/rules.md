# 执行约束规则

本文件记录仓库通用 Harness 开发约束。当前运行时能力以
`docs/ARCHITECTURE.md` 为准；阶段级写入边界和 review 证据分别以
`.harness/allowed_files.md`、`.harness/review_checklist.md` 为准。

## 基本边界

- RepoPilot 是可控 Code Agent Harness，不是通用 AI IDE。
- 一次只推进一个小阶段，不把 Roadmap 能力写成已实现。
- OpenSpec、Superpowers、MCP、plugin 和 `.codex/skills/**` 默认是开发流程，
  不是 RepoPilot runtime 能力。
- 不绕过既有工具、权限、审批、审计和验证边界。
- 不覆盖与当前阶段无关的用户修改。

## 阶段开始

1. 检查当前分支、工作树、最近提交和 active OpenSpec change。
2. 按风险将阶段标为 `low`、`medium` 或 `high`，写明判断依据。
3. 创建或更新一个 OpenSpec change，明确 scope、non-goals、失败行为和验收证据。
4. 先同步 allowed files 和 review checklist，再修改 specs、tests 或 runtime。
5. 只列出事实所有权发生变化的 durable docs，不默认更新所有文档。
6. 普通窄阶段由 Agent 阅读完整 plan/spec 并给用户摘要确认；不要求用户逐字审阅 OpenSpec
   artifacts。高风险、概念模糊、公开行为变化或用户要求时，再提升为完整 plan/spec review。
7. 涉及 MCP、Skill、subagent、connector、runtime plugin、background worker 等容易误解为
   runtime 能力的主题时，先做轻量 Grilling Gate，明确术语、反例、non-goals 和安全边界。

## TDD 与验证

- 行为变更遵循 RED-GREEN-REFACTOR；先看到测试因缺少目标行为而失败。
- 优先运行最小相关测试，runtime/tests 最终变化后运行：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/verify.ps1
```

- 验证无法运行时，必须说明原因和未覆盖风险。
- 测试通过只证明已执行断言，不证明 contract、风险判断或 review 正确。

## Review

- 正式 review 必须晚于最后一次 runtime/test 变更，早于 archive/merge。
- finding 应包含 severity、位置、触发条件、后果和缺失测试。
- 审查层次包括 scope、business logic、architecture boundary、minimality、failure semantics、
  security/privacy、test adequacy 和 maintainability。报告给用户时保留英文工程术语，并给出中文
  解释或例子。
- 外部 review 应寻找独立反例；不得只是重复 tasks 和测试状态。
- 外部 finding 按 `fix / clarify / reject / defer` 分类，并以仓库事实为准。
- `medium/high` 风险阶段默认需要独立外部 review；`low` 风险阶段按需进行。
- runtime 在正式 review 或 archive 后再次变化，旧 review/verification 证据失效。
- Medium/high plan review 保留 internal review 和两个 independent review slots；final implementation
  review 的 required slot 数量继续由风险合同决定。Provider/model 只作为适配器与 residual-risk
  证据，不能替代 reviewer instance 和 context isolation。
- 首轮 reviewer 必须与 implementer/其他 slot 实例分离，审同一冻结 packet，不继承实现上下文，
  也不能先看其他首轮结论。Codex 替代 slot 时使用新的空上下文 task 或 `fork_turns="none"`
  subagent；inherited or unknown context fail closed。开发环境 subagent 不属于 RepoPilot runtime。
- Same-slot remediation re-review 可复用原 reviewer 以保持 finding lineage，但不能增加 slot；
  修复后所有 required slots 的最终回执必须绑定 same final content-addressed baseline；lineage 必须解析
  content-hashed 原始 first-round receipt 的同一 slot/reviewer/finding IDs。
- 实际回执集位于 `.harness/reviews/<stage-id>/<phase>/review-set.json`。Review gate 必须消费：

```text
python scripts/validate_independent_review.py \
  --project-root . \
  --receipt-set .harness/reviews/<stage-id>/<phase>/review-set.json \
  --expected-stage <stage-id> \
  --expected-phase <plan|implementation> \
  --required-slots <risk-contract-count>
```

- 缺失 receipt set、跳过该命令或 validator 非零退出时，任何 independent slot 都不得计为完成。
  Validator 只声明 `mechanical_consistency_only` 并保持 `gate_ready=false`；宿主控制器必须另外核对 native
  dispatch provenance，变更前流程 authority 必须另外核对 activation sequence。仓库 receipt 自填字段不是
  这两项事实的机器证明。
- 新增 validator/gate 的 change 只能由变更前流程 authority 在实现、负样本与 workflow wiring 通过后激活；
  validator 只核对 activation record path/hash，不证明时序，也不得追溯声称它验证了自己实现前的 plan
  review。激活后从该 change 的 final review 和后续适用 review 生效。

## Stage Debt Sweep

- 只检查 changed runtime/tests、其直接依赖或共享状态的 older paths，以及事实发生变化的文档。
- 在 checklist 中记录实际检查路径、finding、处理方式和 residual risk。
- 脚本只覆盖可机械检查的漂移，不得替代人工代码和测试债审查。
- 不在当前 scope 内修复的真实债务写入 `docs/PROGRESS.md`；只有影响下一轮操作时才写入
  `HANDOFF_TO_NEXT_CHAT.md`。

## Archive、Merge 与 Handoff

- archive 冻结已经 review 的 runtime 状态；archive 后 runtime 修复必须重新打开 review gate。
- 连续执行授权只减少中间确认，不跳过 TDD、验证、review、archive 或授权边界。
- commit、merge、push 等操作仍需遵守用户授权和仓库规则。
- merge/push 完成后只做一次 final handoff。
- `docs/PROGRESS.md` 记录长期能力、决策、验证和债务；
  `HANDOFF_TO_NEXT_CHAT.md` 只记录下一轮安全行动所需上下文。
- branch、HEAD、remote 和精确 hash 通过 Git 命令查询，不复制成多份会自失效的文档事实。
- closeout 不创建或暗示下一产品阶段。

## 完成前检查

```powershell
git status --short --branch
git diff --name-only
git diff --check
openspec validate --all
```

再运行当前阶段要求的测试、skill eval、stage docs 或 closeout 检查。
