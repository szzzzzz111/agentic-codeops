# 当前 Harness 写入边界

Active OpenSpec change：无。
最近归档 OpenSpec change：`omit-empty-evidence-snippets`，归档到
`openspec/changes/archive/2026-07-02-omit-empty-evidence-snippets/`。
风险级别：medium。

本阶段已完成 `app/rag/evidence.py` 中 empty / whitespace-only evidence snippet 的
Context Budget 计数语义修正：空 snippet 保留 evidence item 但不计入 included evidence，
不消耗 budget，并计入 omitted。当前处于 archive 后 closeout 状态；除必要的验证记录、
handoff、commit/merge/push closeout 外，不再扩展 scope。

## Archive / Closeout 阶段允许修改

- `.harness/allowed_files.md`
- `.harness/review_checklist.md`
- `docs/PROGRESS.md`
- `HANDOFF_TO_NEXT_CHAT.md`
- `openspec/specs/repo-query-understanding-rag/spec.md`
- `openspec/changes/archive/2026-07-02-omit-empty-evidence-snippets/**`

## 本阶段不允许修改

- `app/rag/evidence.py`，除非 archive-after verification 发现 blocking regression。
- `tests/test_evidence_pack.py`，除非 archive-after verification 发现 blocking regression。
- `app/rag/repo_rag.py`
- `app/harness/kernel.py`
- `app/answering/**`
- `app/providers/**`
- `app/tools/**`
- `app/worktrees/**`
- 其他 `tests/**`，除非 implementation review 证明必须补 adjacent RAG/grounded answer regression。
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
