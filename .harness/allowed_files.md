# 当前 Harness 写入边界

Active OpenSpec change：无。
最近归档 OpenSpec change：`cleanup-control-routing-and-test-names`，归档到
`openspec/changes/archive/2026-07-03-cleanup-control-routing-and-test-names/`。
风险级别：medium。

Scope 仅限 control routing cleanup（控制路由整理）和测试命名清理：把
`app/harness/kernel.py` 中 capability-status（能力状态）识别收拢为内部 deterministic
classifier/helper，保持现有 route、answer 和 `/chat` contract 不变；清理少量历史阶段测试命名；
明确 Assistant Control Surface parser（助手控制面解析器）本阶段不扩展自然语言触发词。

## 本次已完成的 Planning 阶段允许修改

- `openspec/changes/archive/2026-07-03-cleanup-control-routing-and-test-names/**`
- `.harness/allowed_files.md`
- `.harness/review_checklist.md`

## 本次用户批准 implementation 后允许修改

- `app/harness/kernel.py`
- `tests/test_agent_harness_kernel.py`
- `tests/test_assistant_control_surface.py`
- `tests/test_chat_api.py`
- `docs/PROGRESS.md`
- `HANDOFF_TO_NEXT_CHAT.md`
- `openspec/specs/agent-loop-tool-execution/spec.md`，仅 archive 应用 spec delta 后。
- `openspec/specs/assistant-control-surface/spec.md`，仅 archive 应用 spec delta 后。

当前无新的 active implementation scope；后续如启动新阶段，必须重新创建 OpenSpec change 并同步本文件。

## 本阶段不允许修改

- `README.md`
- `docs/ARCHITECTURE.md`
- `docs/FEATURE_LIST.json`
- `app/rag/**`
- `app/answering/**`
- `app/providers/**`
- `app/tools/**`
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
- 不实现 commit/merge/push automation、branch/PR automation、后台任务、runtime subagents、connectors、notifications 或 always-on assistant，除非新阶段明确批准。
- 不执行 `git worktree prune`。
- 不打印、提交或持久化 API key、完整 URL、prompt、EvidencePack、原始回答、完整 diff、patch body、raw exception、traceback、reasoning content、原始 fingerprint、HTTP payload、本机绝对路径、`.git` 路径、DB 路径或 DB/lock 文件路径。
- 不把 OpenSpec、Codex/OpenCode skills、Superpowers、MCP、plugin 写成 RepoPilot runtime 能力。
