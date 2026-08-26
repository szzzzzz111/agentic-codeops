# 当前 Harness 写入边界

Active OpenSpec change：none。`clear-repository-ruff-baseline` 已归档到
`openspec/changes/archive/2026-08-26-clear-repository-ruff-baseline/`。

Planning base：`1743eed4694acd585d2a5ef40d090acf56e2969e`；live `origin/main` 与 authorized old tip：`2c0d0d4e749e16e43d867931c58c6a82be56cf13`。

Risk：`medium`。原 full Ruff 精确基线为 `92 errors / 53 files`，现已清零；semantic subject 已冻结。
历史 authority record 只绑定本阶段被审查的完整 scope，不能被解释为新的写入授权。Closeout 预检确认
epoch 1 的 endpoint hash 误包含命令输出末尾换行；append-only epoch 2 仅把同一实际 origin URL 规范化为
无换行字节的 SHA-256，不改变 endpoint、branch、tip、scope 或 action ceiling，写入后立即冻结。

## 已冻结的 historical exact subject（不得再修改）

- `.harness/allowed_files.md`
- `.harness/review_checklist.md`
- `HANDOFF_TO_NEXT_CHAT.md`
- `docs/PROGRESS.md`
- `openspec/specs/verification-runner/spec.md`
- `app/answering/grounded_answer.py`
- `app/assistant/control_surface.py`
- `app/audit/manager.py`
- `app/audit/store.py`
- `app/cli.py`
- `app/harness/__init__.py`
- `app/harness/capabilities.py`
- `app/harness/kernel.py`
- `app/locks/repo_mutation.py`
- `app/longtask/manager.py`
- `app/longtask/parser.py`
- `app/longtask/planner.py`
- `app/longtask/store.py`
- `app/longtask/types.py`
- `app/memory/manager.py`
- `app/memory/store.py`
- `app/patching/apply.py`
- `app/patching/manager.py`
- `app/patching/parser.py`
- `app/patching/provider.py`
- `app/patching/store.py`
- `app/rag/evidence.py`
- `app/rag/query_rewrite.py`
- `app/rag/query_understanding.py`
- `app/rag/repo_rag.py`
- `app/rag/rerank.py`
- `app/tools/tool_executor.py`
- `app/worktrees/disposal.py`
- `app/worktrees/git_metadata.py`
- `app/worktrees/inspection.py`
- `app/worktrees/manager.py`
- `app/worktrees/promotion.py`
- `app/worktrees/reverification.py`
- `app/worktrees/store.py`
- `evals/live_model_provider/api_smoke.py`
- `evals/live_model_provider/cases.py`
- `evals/live_model_provider/components.py`
- `evals/live_model_provider/core.py`
- `evals/live_model_provider/runner.py`
- `tests/test_agent_harness_kernel.py`
- `tests/test_assistant_control_surface.py`
- `tests/test_chat_api.py`
- `tests/test_live_model_provider_eval.py`
- `tests/test_patch_authoring.py`
- `tests/test_query_rewrite.py`
- `tests/test_repo_mutation_locking.py`
- `tests/test_repo_rag.py`
- `tests/test_repo_rerank.py`
- `tests/test_verified_patch_promotion.py`
- `tests/test_worktree_disposal.py`
- `tests/test_worktree_inspection.py`
- `tests/test_worktree_isolation.py`
- `tests/test_worktree_reverification.py`

## 已冻结的 historical prefix subject（不得再修改）

- `.harness/authority/clear-repository-ruff-baseline/`
- `.harness/reviews/clear-repository-ruff-baseline/`
- `openspec/changes/clear-repository-ruff-baseline/`
- `openspec/changes/archive/2026-08-26-clear-repository-ruff-baseline/`

上述 historical exact/prefix paths 全部冻结。完成本次 freeze-state 记录并重建 final packet 后，唯一可写
evidence tail 是：

- `.harness/reviews/clear-repository-ruff-baseline/implementation/review-set.json`
- `.harness/authority/clear-repository-ruff-baseline/delivery-binding.json`

除此之外，包括已完成的 authority epoch、manifest、inventory、本文件、review checklist、源码、测试、文档、spec
与 archive 在内一律不再写。若 final receipt/binding 无法与冻结 packet 一致，立即停止，不得扩大范围或改写
semantic subject。

## 实施约束

- 先运行 Ruff safe `--fix`；禁止 `--unsafe-fixes`、全局/per-file ignore、blanket `noqa` 和规则降级。为保持既有异常合同，只允许在 `app/longtask/planner.py` 与 `evals/live_model_provider/api_smoke.py` 的三处 frozen TRY004 raise 上使用精确行级 `# noqa: TRY004` 并保留理由。
- 14 处 frozen `except Exception` 都是现有 CLI/orchestration/provider/store/reader 最外层 fail-closed 或 fallback 边界；只允许在这些既有 BLE001 行使用精确行级 `# noqa: BLE001`。其中 worktree disposal 的 best-effort failure-state update 可在同一行精确包含 `S110`；不得用于任何新位置。
- 剩余规则逐项做最小等价修改；异常收窄、loop binding、类型错误和时间解析必须由现有或新增回归证明行为不变。
- 不清理未被当前 92 项命中的邻近风格，不顺手重构，不改变公开输出、错误类型或持久化数据。
- Full pytest、full Ruff、canonical `python -I scripts/verify.py`、两项 scanners、OpenSpec 与 `git diff --check` 全绿后，才进入 independent implementation review。
- P0/P1 清零并冻结 final post-archive packet 后，只允许 review-set/delivery-binding evidence tail；随后才可 commit、ff-only merge 与 exact-old-OID lease push。
