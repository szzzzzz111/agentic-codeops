# 当前 Harness 写入边界

Active OpenSpec change：无。最近归档 change：`derive-capability-status-from-runtime`，
归档到 `openspec/changes/archive/2026-07-06-derive-capability-status-from-runtime/`。
风险级别：medium。

Scope：从真实 runtime primitives（运行时原语）派生 capability-status（能力状态）和
Assistant Control Surface（助手控制面）的当前能力摘要。核心是让能力声明依赖现有
`ToolRegistry` backing tools（支撑工具）和固定安全边界，而不是继续维护互相漂移的静态文案。

## 本阶段 Planning 阶段允许修改

- `openspec/changes/archive/2026-07-06-derive-capability-status-from-runtime/**`
- `.harness/allowed_files.md`
- `.harness/review_checklist.md`

## 用户批准的流程文档调整

- `.codex/skills/repo-stage-workflow/SKILL.md`，仅用于补充 human review depth（人工审查深度）规则；
  不改变本阶段 runtime scope，也不把 workflow 文档写成 RepoPilot runtime 能力。

## 用户批准 implementation 后允许修改

- `app/harness/kernel.py`
- `app/harness/capabilities.py`，如实现需要新增内部 adapter。
- `app/assistant/control_surface.py`
- `tests/test_agent_harness_kernel.py`
- `tests/test_assistant_control_surface.py`
- `tests/test_chat_api.py`
- `docs/PROGRESS.md`
- `HANDOFF_TO_NEXT_CHAT.md`
- `openspec/specs/agent-loop-tool-execution/spec.md`，archive 已应用 spec delta。
- `openspec/specs/assistant-control-surface/spec.md`，archive 已应用 spec delta。

## 本阶段不允许修改

- `README.md`
- `docs/ARCHITECTURE.md`，除非 final review 证明新增 adapter 已成为必须记录的稳定 runtime boundary。
- `docs/FEATURE_LIST.json`
- `app/rag/**`
- `app/answering/**`
- `app/providers/**`
- `app/tools/**`，除非 final review 证明必须同步 `ToolSpec` 以外的工具执行边界。
- `app/memory/**`
- `app/longtask/**`
- `app/patching/**`
- `app/verification/**`
- `app/worktrees/**`
- 其他 `tests/**`，除非 final review 证明必须补 adjacent regression。
- provider runtime、live eval profile、默认 CI、public `/chat` contract

## 长期禁止行为

- 不修改 `/chat` public contract、默认 CI、provider runtime 或 live eval profile，除非新阶段 OpenSpec 明确批准。
- 不新增网络依赖，不要求 provider API key，不运行 live gate。
- 不实现 MCP server、MCP tool discovery、动态工具注册、Skill execution、connector、runtime subagent、background worker、notifications、always-on assistant、commit/merge/push automation 或 branch/PR automation。
- 不执行 `git worktree prune`。
- 不打印、提交或持久化 API key、完整 URL、prompt、EvidencePack、原始回答、完整 diff、patch body、raw exception、traceback、reasoning content、原始 fingerprint、HTTP payload、本机绝对路径、`.git` 路径、DB 路径或 DB/lock 文件路径。
- 不把 OpenSpec、Codex/OpenCode skills、Superpowers、MCP、plugin 或 descriptor-only 概念写成 RepoPilot runtime 能力。
