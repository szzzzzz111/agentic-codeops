# V3 实现阶段允许文件

- `specs/003-agent-loop/spec.md`
- `specs/003-agent-loop/plan.md`
- `specs/003-agent-loop/tasks.md`
- `app/agents/code_agent.py`
- `app/tools/__init__.py`
- `app/tools/tool_executor.py`
- `tests/test_chat_api.py`
- `README.md`
- `AGENTS.md`
- `docs/ARCHITECTURE.md`
- `docs/AGENT_RULES.md`
- `.harness/allowed_files.md`
- `.harness/review_checklist.md`
- `docs/PROGRESS.md`
- `HANDOFF_TO_NEXT_CHAT.md`
- `docs/FEATURE_LIST.json`

本阶段只允许实现 V3 最小确定性 Agent Loop，不开放写文件工具、shell 工具、真实 LLM、多 Agent、RAG、Memory、Reflection 或 eval。
