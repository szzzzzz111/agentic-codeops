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
- 外部 review 应寻找独立反例；不得只是重复 tasks 和测试状态。
- 外部 finding 按 `fix / clarify / reject / defer` 分类，并以仓库事实为准。
- `medium/high` 风险阶段默认需要独立外部 review；`low` 风险阶段按需进行。
- runtime 在正式 review 或 archive 后再次变化，旧 review/verification 证据失效。

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
