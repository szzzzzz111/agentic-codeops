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
- 端到端阶段使用 `repo-stage-workflow`；planning、review、handoff skill 各自只承担单一职责。
- 实现确认前必须对 proposal、design、tasks、spec deltas、测试计划和 Harness 边界做一次内部
  plan review；OpenSpec validation 不替代该语义检查。

## 验证与 Review

- 行为变更先写失败测试，再做最小实现。
- 默认完整验证：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/verify.ps1
```

- 正式 review 必须针对最终 runtime/test 状态，并在 archive/merge 前完成。
- 测试、OpenSpec validation、checklist marker 和零散自检不能替代正式 review。
- 外部 reviewer 应寻找独立反例；finding 按 `fix / clarify / reject / defer` 处理。
- archive 后如再改 runtime，必须重新验证、review，并重新判断 archive readiness。

## Stage Debt Sweep

- 复核 changed paths 和它们直接依赖、共享状态或调用的 older paths。
- 记录真实检查范围、findings、处理方式和剩余风险，不进行无目标全仓扫描。
- 脚本只证明可机械搜索的约束，不证明语义判断正确。
- 长期债务记录在 `docs/PROGRESS.md`；只有会影响下一轮行动时才同时进入 HANDOFF。

## 文档职责

- `.harness/review_checklist.md`：过程步骤和 gate 证据。
- `docs/PROGRESS.md`：长期能力、重要决策、验证和未清债务。
- `HANDOFF_TO_NEXT_CHAT.md`：下一轮必须知道的当前上下文、阻塞和安全下一步。
- Git/OpenSpec 命令：实时 branch、HEAD、remote、active change 状态。

不是每个 session 都必须修改 PROGRESS 和 HANDOFF。只有各自拥有的事实发生变化时才更新；
archive、merge、push 和分支清理完成后合并为一次 final handoff，不在多份文档重复动态 hash。

## 连续执行授权

用户授权“一路做到 merge/push”时，可以减少中间确认，但不得跳过 TDD、验证、正式 review、
Stage Debt Sweep、archive 检查或高风险 Git 操作的授权边界。发现 P0/P1 或 Git 状态异常时立即
停止 closeout，修复并重新验证、review。
