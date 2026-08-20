# Agent 工作规则

本仓库使用 Harness Engineering 管理 AI 辅助开发。详细运行时架构见
`docs/ARCHITECTURE.md`，具体执行约束见 `.harness/rules.md`。

## 分支与修改

- `main` 保留稳定版本；阶段开发使用独立 feature/worktree。
- 修改前确认分支、工作树、最近提交和 active OpenSpec change。
- 不覆盖无关未提交修改，不混入下一阶段功能，不提交临时产物。
- 严格遵守 `.harness/allowed_files.md`。
- 新阶段先同步 allowed files 和 review checklist，再修改 specs、tests 或 runtime。
- 文档和用户可见文字优先中文；代码标识符和 API 字段使用英文工程约定。

## 风险与流程

- `low`：文档、本地 skill、确定性流程检查；内部 review 为主。
- `medium`：局部 runtime 行为，公开 contract 基本稳定；增加聚焦外部 review。
- `high`：Git/subprocess、持久化、权限、patch 生命周期、公开 API；要求完整独立对抗式 review。
- 风险分级只调整 review 深度，不取消 TDD、验证和安全边界。
- 普通窄阶段默认由 Agent 阅读完整 OpenSpec artifacts，并向用户输出高信号中文摘要和一个
  implementation confirmation gate；用户不需要逐字审 proposal/design/tasks/spec，除非风险、scope
  或用户要求使其必要。
- MCP、Skill、subagent、connector、runtime plugin、background worker、always-on assistant 等
  容易膨胀或误导的主题，应在 OpenSpec 落笔前使用轻量 Grilling Gate（需求拷问关）压实术语、
  scope、反例、runtime availability、approval/audit boundary 和 non-goals。普通 bugfix、文档修正、
  已知窄代码债不默认运行该 gate。
- 端到端阶段使用 `repo-stage-workflow`；planning、review、handoff skill 各自只承担单一职责。
- 实现确认前必须对 proposal、design、tasks、spec deltas、测试计划和 Harness 边界完成
  plan review；medium/high 阶段默认包含 internal plan review 和两个独立 plan-review slots。
  Reviewer provider 是适配器，不是门禁 authority；OpenSpec validation 不替代该语义检查。
- 首轮独立 reviewer 必须与 implementer 和其他 reviewer 实例分离、审阅同一个冻结 packet、
  不继承实现对话且看不到其他首轮结论。Codex 可使用新的空上下文 task，或显式
  `fork_turns="none"` 的 subagent；inherited/unknown context 不得计数。这里的 task/subagent
  只属于 development workflow，不是 RepoPilot runtime capability。
- Remediation re-review 可以复用产生 finding 的原 reviewer 会话，但仍只占原 slot；修复后
  每个 required slot 都必须刷新到 same final content-addressed baseline。适配器失败时换用另一个
  独立实例，不能减少 required slot 数量。Receipt 必须通过 content-hashed `review_history` 解析到原
  first-round receipt 的同一 slot/reviewer/finding IDs。
- 实际回执集固定写入 `.harness/reviews/<stage-id>/<phase>/review-set.json`，并运行
  `python scripts/validate_independent_review.py --project-root . --receipt-set <path> --expected-stage <stage-id> --expected-phase <plan|implementation> --required-slots <count>`。
  Receipt 缺失、命令未运行或非零退出时 review gate 保持打开。Validator 只给出
  `mechanical_consistency_only`，固定 `gate_ready=false`；宿主控制器还必须直接核对 native dispatch
  metadata，变更前流程 authority 必须核对 activation sequence。仓库内自填字段不能单独证明这两项事实。
- OpenCode 首轮必须使用新的隔离 review session，或提供宿主证据证明候选 session 没有实现对话和
  其他 reviewer 结论；`opencode session list` 与 `opencode run --session <session_id> ...` 只用于
  same-slot remediation re-review 或恢复同一次 timeout。超时本身不是 verdict，必须检查 final
  assistant review text。

## 验证与 Review

- 行为变更先写失败测试，再做最小实现。
- 默认完整验证：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/verify.ps1
```

- 正式 final implementation review 必须针对最终 runtime/test 状态，并在 archive/merge 前完成；
  它不能替代实现前 plan review，plan review 也不能替代最终实现 review。
- Final implementation review 的 required slot 数量由阶段风险合同决定；每一个 required slot
  都必须满足相同的实例/上下文隔离、冻结 packet、回执和 validator 合同。Medium/high plan review
  的两个独立 slots 不应被误写成所有 final review 都固定两个 slots。
- 测试、OpenSpec validation、checklist marker 和零散自检不能替代正式 review。
- Code review（代码审查）应覆盖需求范围、业务逻辑、架构边界、最小功能、失败语义、安全/隐私、
  测试充分性和可维护性。Agent 默认负责底层实现、测试、安全和维护性审查，并把结论翻译成用户
  可判断的中文摘要；用户主要确认方向、边界、行为语义、风险接受和残余风险。
- 外部 reviewer 应寻找独立反例；plan finding 和 implementation finding 都按
  `fix / clarify / reject / defer` 处理。
- archive 后如再改 runtime，必须重新验证、review，并重新判断 archive readiness。

## Stage Debt Sweep

- 复核 changed paths 和它们直接依赖、共享状态或调用的 older paths。
- 记录真实检查范围、findings、处理方式和剩余风险，不进行无目标全仓扫描。
- 脚本只证明可机械搜索的约束，不证明语义判断正确。
- 长期债务记录在 `docs/PROGRESS.md`；只有会影响下一轮行动时才同时进入 HANDOFF。

## 文档职责

- `README.md`：项目门面、当前 capability snapshot、quick start 和文档导航；不承载详细阶段历史。
- `docs/ARCHITECTURE.md`：稳定 runtime boundary 和 durable component relationships；不把 transient stage task 写成当前事实。
- `docs/FEATURE_LIST.json`：acceptance-oriented capability inventory 和 `passes` 状态；不写路线图叙事。
- `.harness/review_checklist.md`：过程步骤和 gate 证据。
- `docs/PROGRESS.md`：长期能力、重要决策、验证和未清债务。
- `HANDOFF_TO_NEXT_CHAT.md`：下一轮必须知道的当前上下文、阻塞和安全下一步。
- Git/OpenSpec 命令：实时 branch、HEAD、remote、active change 状态。

不是每个 session 都必须修改 PROGRESS 和 HANDOFF。只有各自拥有的事实发生变化时才更新；
archive、merge、push 和分支清理完成后合并为一次 final handoff，不在多份文档重复动态 hash。
Archived OpenSpec changes 和 `docs/PROGRESS.md` 历史段落可以保留当时真实的旧路线图措辞；
current-state drift scan 只应针对当前事实文件和当前建议段。

## 连续执行授权

用户授权“一路做到 merge/push”时，可以减少中间确认，但不得跳过 TDD、验证、正式 review、
Stage Debt Sweep、archive 检查或高风险 Git 操作的授权边界。发现 P0/P1 或 Git 状态异常时立即
停止 closeout，修复并重新验证、review。
