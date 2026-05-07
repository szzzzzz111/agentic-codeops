# Agent 入口地图

本文件是给 Codex、OpenCode、Copilot Agent 等工具看的入口地图，不是百科全书。进入本仓库后，先按下面顺序阅读。

## 必读顺序

1. `README.md`：项目简介、当前能力和路线图。
2. `docs/PROGRESS.md`：当前阶段、已完成内容和阻塞点。
3. `docs/ARCHITECTURE.md`：架构边界和后续演进方向。
4. `docs/AGENT_RULES.md`：Agent 工作规则、分支规则和禁止项。
5. `docs/FEATURE_LIST.json`：可验收功能清单。
6. `.harness/allowed_files.md`：当前阶段允许修改的文件。
7. `.harness/review_checklist.md`：当前阶段 review 清单。
8. `HANDOFF_TO_NEXT_CHAT.md`：交接给下一轮 session 的上下文。

## 工作原则

- 一次只做一个小阶段，不跨阶段扩功能。
- 先确认当前分支，再修改代码。
- 优先跑确定性验证：`pytest`、`ruff check .`、`scripts/verify.ps1`。
- 修改结束后更新 `docs/PROGRESS.md` 和 `HANDOFF_TO_NEXT_CHAT.md`。
- 不要把项目知识只留在聊天窗口里，必须沉淀到仓库文档。

## 当前默认验证命令

```powershell
powershell -ExecutionPolicy Bypass -File scripts/verify.ps1
```
