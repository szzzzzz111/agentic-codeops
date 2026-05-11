# V4 实现阶段允许文件

- `specs/004-skill-loader/spec.md`
- `specs/004-skill-loader/plan.md`
- `specs/004-skill-loader/tasks.md`
- `app/tools/skill_loader.py`
- `tests/test_skill_loader.py`
- `.harness/allowed_files.md`
- `.harness/review_checklist.md`
- `.harness/rules.md`
- `AGENTS.md`
- `docs/AGENT_RULES.md`
- `docs/PROGRESS.md`
- `HANDOFF_TO_NEXT_CHAT.md`
- `README.md`
- `docs/FEATURE_LIST.json`

本阶段只允许实现 V4 Skill Metadata Loader 及其测试，不开放其他运行时代码、API handler、Agent loop、Service 层或 `/chat` 决策修改。

V4 实现必须保持 metadata-first：只发现 `.agents/skills/*/SKILL.md`，解析 `name`、`description` 和相对仓库 `path`。不得执行 skill，不得读取或返回完整 skill 正文，不得做 progressive disclosure，不得接真实 LLM、RAG、Memory、Reflection、eval 或复杂多 Agent。
