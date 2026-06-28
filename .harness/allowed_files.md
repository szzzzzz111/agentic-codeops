# 当前 Harness 写入边界

Active OpenSpec change：无。
最近归档 OpenSpec change：`harden-worktree-create-timeouts`；风险级别：high。

该阶段已完成 V20 worktree create / workspace preflight / rollback Git subprocess
timeout 与 bounded output hardening。

## 当前允许修改

- `.harness/allowed_files.md`
- `.harness/review_checklist.md`
- `docs/PROGRESS.md`
- `HANDOFF_TO_NEXT_CHAT.md`
- `openspec/changes/archive/2026-06-28-harden-worktree-create-timeouts/**`
- `openspec/specs/worktree-isolation/spec.md`

## 最近阶段已修改

- `app/worktrees/manager.py`
- `tests/test_worktree_isolation.py`

## 本阶段不允许修改

- `app/worktrees/inspection.py`
- `app/worktrees/disposal.py`
- `app/worktrees/reverification.py`
- `app/worktrees/promotion.py`
- `app/harness/kernel.py`
- `app/tools/**`
- `app/verification/**`
- 其他 `tests/**`
- `README.md`
- `docs/ARCHITECTURE.md`
- `docs/FEATURE_LIST.json`
- provider runtime、live eval profile、默认 CI、public `/chat` contract

## 长期禁止行为

- 不修改 `/chat` public contract、默认 CI、provider runtime 或 live eval profile，除非新阶段 OpenSpec 明确批准。
- 不新增网络依赖，不要求 provider API key，不运行 live gate。
- 不实现 commit/merge/push automation、branch/PR automation、后台任务、runtime subagents、connectors、notifications 或 always-on assistant，除非新阶段明确批准。
- 不执行 `git worktree prune`。
- 不打印、提交或持久化 API key、完整 URL、prompt、EvidencePack、原始回答、完整 diff、patch body、raw exception、traceback、reasoning content、原始 fingerprint、HTTP payload、本机绝对路径、`.git` 路径、DB 路径或 DB/lock 文件路径。
- 不把 OpenSpec、Codex/OpenCode skills、Superpowers、MCP、plugin 写成 RepoPilot runtime 能力。
