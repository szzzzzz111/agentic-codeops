# 当前 Harness 写入边界

当前阶段：V7 `v7-permission-approval-gate`

## 允许修改

- OpenSpec change:
  - `openspec/changes/v7-permission-approval-gate/**`
- Harness:
  - `.harness/allowed_files.md`
  - `.harness/review_checklist.md`
- Runtime:
  - `app/harness/kernel.py`
- Tests:
  - `tests/test_agent_harness_kernel.py`
  - `tests/test_chat_api.py`
- Docs:
  - `README.md`
  - `docs/ARCHITECTURE.md`
  - `docs/PROGRESS.md`
  - `docs/FEATURE_LIST.json`
  - `HANDOFF_TO_NEXT_CHAT.md`

## 禁止修改

- 不恢复旧 `specs/00x-*` 作为规格入口。
- 不把 OpenSpec、Superpowers、MCP、plugin 或外部 skill 误写成 RepoPilot runtime 能力。
- 不实现真实审批 UI、审批持久化、写文件工具、删文件工具、shell 工具或 SandboxRunner。
- 不提前实现 LLM、RAG、Memory、Reflection、skill execution、eval 或复杂多 Agent。
- 不新增 `/chat` 顶层响应字段。
