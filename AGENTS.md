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
9. 如本轮涉及新阶段规划，读取 `openspec/README.md` 并按项目级 OpenSpec 流程创建 change artifacts。

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
- `openspec/README.md`：本仓库项目级 OpenSpec 使用说明；OpenSpec 是开发流程，不是 RepoPilot runtime 功能。
- `openspec/specs/`：长期能力规格入口，承接已迁移的 V1-V4 legacy specs。
- `openspec/changes/archive/`：已归档 OpenSpec changes 和历史迁移记录。
- `.codex/skills/`：本仓库内 Codex OpenSpec skills；只在项目内使用，不安装全局 Codex prompts。
- `.opencode/`：本仓库内 OpenCode OpenSpec commands 和 skills。
- 旧 `specs/00x-*`：已迁移并退役，不再作为当前规格入口。

## 工作原则

- 一次只做一个小阶段，不跨阶段扩功能。
- 新阶段优先使用项目级 OpenSpec 创建 proposal/design/tasks，再同步 `.harness/allowed_files.md` 和 `.harness/review_checklist.md`。
- 先确认当前分支，再修改代码。
- 新阶段开始前，先同步 `.harness/allowed_files.md` 和 `.harness/review_checklist.md`。
- 优先维护 Harness 边界：工具调用、审计字段、specs、review checklist 和 handoff 必须与代码一致。
- 优先跑确定性验证：`pytest`、`ruff check .`、`scripts/verify.ps1`。
- 修改结束后更新 `docs/PROGRESS.md` 和 `HANDOFF_TO_NEXT_CHAT.md`。
- 提交前检查 `git status --short --branch`、`git diff --name-only` 和 `git diff --check`，避免无语义 diff 或阶段混杂。
- 不要把项目知识只留在聊天窗口里，必须沉淀到仓库文档。
- OpenSpec、Superpowers、MCP、plugin 等外部范式默认只作为开发流程参考；除非阶段 specs 明确开放，不得写成 RepoPilot 产品运行时能力。
- 本仓库当前不保留 `.github` OpenSpec prompts/skills；Copilot 对接不通过仓库内 `.github` 生成物维护。

## 当前默认验证命令

```powershell
powershell -ExecutionPolicy Bypass -File scripts/verify.ps1
```
