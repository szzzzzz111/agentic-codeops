# Agent 工作规则

本项目使用 Harness Engineering 思路管理 AI 辅助开发：让 Agent 通过规则、文档、验证和交接机制稳定工作。RepoPilot 的定位是可控 Code Agent Harness，不是替代通用 AI 编程助手；实现时应优先保护工具调用边界、审计字段、验证规则和跨 session 交接质量。

## 分支规则

- `main` 只保留稳定可运行版本。
- `dev` 用于集成已完成阶段。
- 当前功能必须在 `feature/*` 分支开发。
- 每轮实现前先确认当前分支。
- 如果当前不在正确 feature 分支，先暂停并提醒用户，不直接修改代码。

## 修改规则

- 严格遵守 `.harness/allowed_files.md`。
- 新阶段开始前必须先更新 `.harness/allowed_files.md` 和 `.harness/review_checklist.md`，再修改 specs 或代码。
- 不要跨阶段实现未来功能。
- 不要把所有逻辑堆进 `main.py`。
- 不要提交缓存文件、虚拟环境、本地环境变量或临时产物。
- 文档、注释和用户可见文案优先使用中文。
- 函数名、类名、接口字段和命令保持英文工程约定。
- 不要把上一阶段收尾文档和下一阶段功能实现混在同一个 commit。
- 如果 handoff、progress、specs 或 harness 仍指向旧分支/旧阶段，先同步文档再继续实现。

## 验证规则

优先使用确定性检查，不要只靠 LLM review。

当前最低验证：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/verify.ps1
```

该脚本至少应运行：

- `pytest`
- `ruff check .`，如果当前环境已安装 ruff

如果某个检查无法运行，最终说明必须写清楚原因。

## 交接规则

每轮结束必须更新：

- `docs/PROGRESS.md`
- `HANDOFF_TO_NEXT_CHAT.md`
- 必要时更新 `docs/FEATURE_LIST.json`

交接内容至少包含：

- 当前分支。
- 本轮完成内容。
- 修改文件。
- 验证命令和结果。
- 未完成事项。
- 下一轮建议。

## Review 规则

Review Agent 必须检查：

- 是否符合当前阶段 scope。
- 是否修改了不该改的文件。
- 是否真的运行了验证命令。
- 是否存在假实现或过度设计。
- 是否破坏架构边界。
- 是否把 Roadmap 能力写成已实现。
- 是否让工具调用绕过 `ToolExecutor` 或堆到 API 层。
- 是否 handoff、progress、specs、harness 与当前分支和阶段一致。
- 是否存在无语义 diff，例如只改行尾或无内容变化的文件。
- 是否更新测试和文档。
- 是否更新 progress 和 handoff。

## Stage Debt Sweep 规则

- 每个阶段收口前必须人工复核 changed runtime/tests 以及它依赖的 adjacent older paths，不能只检查新增文件。
- `scripts/check_stage_docs.ps1`、`scripts/check_stage_closeout.ps1` 等脚本只覆盖机械可搜索、可确定性表达的债务。
- 脚本、测试和 checklist 通过不能替代人工代码/测试债审查，也不能单独证明 Stage Debt Sweep 完成。
- 人工发现的债务必须在当前 scope 内修复，或记录到 `docs/PROGRESS.md` 与
  `HANDOFF_TO_NEXT_CHAT.md`；不得只留在聊天中。

## 连续执行授权与正式 Review 门

- 用户对“继续实现到提交 / 归档 / 合并 / 推送”的连续执行授权，只减少阶段级确认次数，不替代任何 review、Stage Debt Sweep、验证或 closeout gate。
- 正式 code review 必须在最终 runtime / tests 变更之后、archive / merge 之前重新执行，并明确输出 findings，或明确输出“无 findings”及剩余风险。
- 仅有测试通过、零散自检、任务勾选或口头声称 review 完成，均不构成正式 review 证据。
- 如果正式 review 在 merge 后发现 P0/P1，必须立即把 finding 记录到 `.harness/review_checklist.md`、`docs/PROGRESS.md` 和 `HANDOFF_TO_NEXT_CHAT.md`，将 closeout 恢复为阻断状态，并在修复、复核和验证完成前禁止开始下一阶段。
