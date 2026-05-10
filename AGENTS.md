# Agent 入口地图

本文件是给 Codex、OpenCode、Copilot Agent 等工具看的入口地图，不是百科全书。RepoPilot 当前定位是面向代码仓库分析任务的可控 Code Agent Harness：重点不是替代通用 AI 编程助手，而是沉淀工具调用边界、审计字段、验证规则和交接机制。进入本仓库后，先按下面顺序阅读。

## 必读顺序

1. `README.md`：项目简介、当前能力和路线图。
2. `docs/PROGRESS.md`：当前阶段、已完成内容和阻塞点。
3. `docs/ARCHITECTURE.md`：架构边界和后续演进方向。
4. `docs/AGENT_RULES.md`：Agent 工作规则、分支规则和禁止项。
5. `docs/FEATURE_LIST.json`：可验收功能清单。
6. `.harness/allowed_files.md`：当前阶段允许修改的文件。
7. `.harness/review_checklist.md`：当前阶段 review 清单。
8. `HANDOFF_TO_NEXT_CHAT.md`：交接给下一轮 session 的上下文。

## 文档职责

- `AGENTS.md`：入口地图和文档职责说明，不写详细架构或阶段任务。
- `README.md`：面向人类的项目定位、当前能力、启动方式和路线图。
- `docs/ARCHITECTURE.md`：当前真实架构、边界和扩展点，不把 Roadmap 写成已实现。
- `docs/PROGRESS.md`：当前阶段状态、已完成内容、最近验证和下一步建议。
- `docs/AGENT_RULES.md`：长期协作规则，包括分支、修改、验证、交接和 review。
- `docs/FEATURE_LIST.json`：可验收功能清单和 `passes` 状态，不写长篇设计解释。
- `HANDOFF_TO_NEXT_CHAT.md`：下一轮 session 的操作上下文，不替代长期文档。
- `.harness/rules.md`：本仓库执行约束和 TDD/Harness 纪律。
- `.harness/allowed_files.md`：当前阶段允许修改的文件，不写设计理由或历史内容。
- `.harness/review_checklist.md`：当前阶段 review 检查项，不写实现方案。
- `.harness/test_commands.md`：验证命令集合，不记录测试结果。
- `specs/00x-*/spec.md`：该阶段要做什么、不做什么和验收标准。
- `specs/00x-*/plan.md`：该阶段怎么做、改哪些模块和执行顺序。
- `specs/00x-*/tasks.md`：该阶段 TDD checklist，不写项目定位或长期路线图。

## 工作原则

- 一次只做一个小阶段，不跨阶段扩功能。
- 先确认当前分支，再修改代码。
- 新阶段开始前，先同步 `.harness/allowed_files.md` 和 `.harness/review_checklist.md`。
- 优先维护 Harness 边界：工具调用、审计字段、specs、review checklist 和 handoff 必须与代码一致。
- 优先跑确定性验证：`pytest`、`ruff check .`、`scripts/verify.ps1`。
- 修改结束后更新 `docs/PROGRESS.md` 和 `HANDOFF_TO_NEXT_CHAT.md`。
- 提交前检查 `git status --short --branch`、`git diff --name-only` 和 `git diff --check`，避免无语义 diff 或阶段混杂。
- 不要把项目知识只留在聊天窗口里，必须沉淀到仓库文档。

## 当前默认验证命令

```powershell
powershell -ExecutionPolicy Bypass -File scripts/verify.ps1
```
