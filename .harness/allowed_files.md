# 当前 Harness 写入边界

当前阶段：V5 Skill Content Loader / progressive disclosure 规划与实现。

对应 OpenSpec change：

- `openspec/changes/v5-skill-content-loader/`

本阶段允许修改：

- `.harness/allowed_files.md`
- `.harness/review_checklist.md`
- `openspec/changes/v5-skill-content-loader/**`
- `README.md`
- `app/tools/skill_loader.py`
- `tests/test_skill_loader.py`
- `docs/PROGRESS.md`
- `docs/FEATURE_LIST.json`
- `HANDOFF_TO_NEXT_CHAT.md`

本阶段禁止修改：

- 不恢复旧 `specs/00x-*` 作为规格入口。
- 不修改长期 `openspec/specs/`，除非归档当前 change 时由 OpenSpec 流程生成。
- 不接入 `/chat`、`CodeAgent` 或 `ToolExecutor` 决策。
- 不执行 skill，不接真实 LLM，不自动把 skill 内容注入 prompt。
- 不引入 RAG、Memory、Reflection、eval、PermissionPolicy、ApprovalGate 或 SandboxRunner。
- 不把 OpenSpec、Superpowers、MCP、plugin 或外部 skill 写成 RepoPilot runtime 能力。
