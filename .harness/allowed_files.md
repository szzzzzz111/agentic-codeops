# 当前 Harness 写入边界

Active OpenSpec change：无。
最近归档 OpenSpec change：`parameterize-hybrid-fusion-settings`，归档到
`openspec/changes/archive/2026-07-03-parameterize-hybrid-fusion-settings/`。
风险级别：medium。

Scope 仅限 `app/rag/repo_rag.py` 中 hybrid fusion settings（hybrid fusion 的混合打分配方）
参数化，以及 `ToolExecutor` 对有效 settings 的内部 audit summary 透传：把 lexical /
embedding 权重和 `min_fused_score` 从分散默认值收束为显式、可校验、可审计的
deterministic settings。默认行为必须保持不变，不新增 `/chat` 字段、网络依赖或用户可调 API。

## Planning 阶段允许修改

- `openspec/changes/parameterize-hybrid-fusion-settings/**`
- `.harness/allowed_files.md`
- `.harness/review_checklist.md`

## 用户批准 implementation 后允许修改

- `app/rag/repo_rag.py`
- `app/tools/tool_executor.py`
- `tests/test_repo_rag.py`
- `tests/test_tool_executor.py`
- `tests/test_agent_harness_kernel.py`，仅用于 final review 要求的 adjacent AgentLoop trace regression。
- `docs/PROGRESS.md`
- `HANDOFF_TO_NEXT_CHAT.md`
- `openspec/specs/repo-query-understanding-rag/spec.md`，仅 archive 应用 spec delta 后。

## 本阶段不允许修改

- `app/rag/query_understanding.py`
- `app/rag/query_rewrite.py`
- `app/rag/rerank.py`
- `app/rag/evidence.py`
- `app/answering/**`
- `app/providers/**`
- `app/harness/kernel.py`
- `app/tools/**`，但允许上文列出的 `app/tools/tool_executor.py`。
- `app/worktrees/**`
- 其他 `tests/**`，除非 implementation review 证明必须补 adjacent AgentLoop/API RAG contract regression。
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
