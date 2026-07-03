## 1. Planning And Harness

- [x] 1.1 Confirm branch, worktree, recent commits, remote sync, and active OpenSpec state.
- [x] 1.2 Read `AGENTS.md`, required project docs, OpenSpec README, Harness rules, and workflow/planning skills.
- [x] 1.3 Select the next small code debt: hybrid fusion weights and threshold should be explicit settings.
- [x] 1.4 Create proposal, design, tasks, and spec delta.
- [x] 1.5 Synchronize `.harness/allowed_files.md` and `.harness/review_checklist.md`.
- [x] 1.6 Run internal plan review and classify findings as `fix`, `clarify`, `reject`, or `defer`.

Plan findings:

- `fix`（internal）：test plan incorrectly said a higher threshold could make an embedding-only result pass; corrected to deterministic pass/filter behavior and lexical/embedding score mix.
- `clarify`（OpenCode）：settings must be the single source of truth when provided, while standalone compatibility kwargs apply only when `settings` is omitted; clarified in design.
- `clarify`（OpenCode）：`max_results` remains a per-call cap rather than a fusion settings field; clarified in design.
- `clarify`（OpenCode）：settings validation is construction-time fail fast; clarified in design.
- `fix`（Codex）：allowed files were too narrow to fulfill the internal audit/trace contract because `ToolExecutor` aggregation did not preserve new effective weight fields; expanded scope to `app/tools/tool_executor.py` and `tests/test_tool_executor.py`, and added audit pass-through tests to the plan.
- `clarify`（Codex）：tasks/checklist had recorded OpenCode findings while the OpenCode review gate still showed pending; gate records now mark OpenCode plan review as complete.
- [x] 1.7 Run Codex independent plan review and classify findings as `fix`, `clarify`, `reject`, or `defer`.
- [x] 1.8 Run `opencode session list` and OpenCode independent plan review using session reuse rules; classify findings as `fix`, `clarify`, `reject`, or `defer`.
- [x] 1.9 Run `openspec validate parameterize-hybrid-fusion-settings --strict`.
- [x] 1.10 Stop at implementation confirmation gate.

Implementation gate:

- User confirmed continuing code-debt work in this thread; no additional product decision is open.

## 2. Implementation After Approval

- [x] 2.1 Add RED tests for default settings preserving current scores and order.
- [x] 2.2 Add RED tests for custom fusion settings and retriever audit summary.
- [x] 2.3 Add RED tests for ToolExecutor internal audit pass-through without public call_summary exposure.
- [x] 2.4 Add RED tests for invalid settings validation.
- [x] 2.5 Preserve lexical anchor and public contract regressions.
- [x] 2.6 Implement the smallest `HybridFusionSettings` and resolver change.
- [x] 2.7 Update durable documentation only for facts that changed.

## 3. Review, Verification, Archive

- [x] 3.1 Run focused `pytest tests/test_repo_rag.py -q`.
- [x] 3.2 Run adjacent AgentLoop/API RAG contract tests if needed.
- [x] 3.3 Run `ruff check .`.
- [x] 3.4 Run `openspec validate --all`.
- [x] 3.5 Run `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`.
- [x] 3.6 Run `git diff --check`.
- [x] 3.7 Run final implementation review after the last runtime/test change.
- [x] 3.8 Perform focused Stage Debt Sweep over changed runtime/tests/docs/specs/Harness and directly dependent paths.
- [x] 3.9 Archive the OpenSpec change only after blocking findings are closed and validation passes.

Final implementation review findings:

- `fix`（Codex）：final verification / review checklist / progress / handoff status had not yet been backfilled after implementation verification；本记录、`.harness/review_checklist.md`、`docs/PROGRESS.md` 和 `HANDOFF_TO_NEXT_CHAT.md` 已补齐。
- OpenCode final implementation review：no `fix` / `clarify` / `reject` / `defer` findings；no blocking findings。
- `fix`（Stage Debt Sweep）：`ToolExecutor` 不应在 retriever 未提供 fusion settings 时合成默认 audit values；已改为仅复制明确提供的 effective settings，并补 `tests/test_tool_executor.py` regression。
- `fix`（Stage Debt Sweep）：AgentLoop internal trace regression 只覆盖 `min_fused_score`，未覆盖新增 `lexical_weight` / `embedding_weight`；已补 `tests/test_agent_harness_kernel.py` adjacent regression，并同步 allowed files。

Final verification evidence:

- Focused/adjacent `pytest tests/test_repo_rag.py tests/test_tool_executor.py tests/test_agent_harness_kernel.py tests/test_chat_api.py -q`：100 passed。
- `ruff check .`：passed。
- `openspec validate --all`：23 passed，0 failed。
- Full `powershell -ExecutionPolicy Bypass -File scripts\verify.ps1`：pytest 517 passed，1 skipped；ruff、stage docs scan、skill eval structure scan passed。
- `git diff --check`：passed，仅 CRLF normalization warnings。

Stage Debt Sweep:

- 覆盖 changed runtime/tests/docs/OpenSpec/Harness：`app/rag/repo_rag.py`、`app/tools/tool_executor.py`、`tests/test_repo_rag.py`、`tests/test_tool_executor.py`、active OpenSpec artifacts、`.harness/allowed_files.md`、`.harness/review_checklist.md`、`docs/PROGRESS.md`、`HANDOFF_TO_NEXT_CHAT.md`。
- 覆盖直接依赖：`app/harness/kernel.py` 的 `call_summary()` public tool call 边界和 internal trace/audit summary 路径。
- 结论：Stage Debt Sweep 的两个 `fix` findings 已关闭。`HybridFusionSettings` defaults、custom mix/threshold、construction-time validation、internal audit pass-through、no synthesized missing audit settings、AgentLoop internal trace 和 public `call_summary()` separation 均有测试覆盖。

Fix verification:

- Codex fix verification：两个 Stage Debt Sweep `fix` findings 均已关闭；no new findings。
- OpenCode fix verification：复用 `ses_1018bd2aeffeKLTCcQhhuQ1jFZ`；两个 Stage Debt Sweep `fix` findings 均已关闭；no findings。
