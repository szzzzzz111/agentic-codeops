# 当前 Review 清单

Active OpenSpec change：无。
最近归档 OpenSpec change：`cleanup-control-routing-and-test-names`，归档到
`openspec/changes/archive/2026-07-03-cleanup-control-routing-and-test-names/`。
风险级别：medium。

目标是一次小修正清理剩余代码债：capability-status（能力状态）识别收拢为内部
classifier/helper；历史阶段命名测试改成更稳定的能力命名；Assistant Control Surface parser
保持小而明确，本阶段不扩展自然语言触发词。

## Planning / Harness

- [x] 已读取 `AGENTS.md`、必读文档、OpenSpec README、Harness rules、workflow/planning skills。
- [x] 已检查 branch、worktree、recent commits、remote sync 和 active OpenSpec changes。
- [x] 已选择小代码债：control routing cleanup + test naming cleanup，不扩展状态问法。
- [x] 已创建 OpenSpec proposal、design、tasks、spec delta。
- [x] 已同步 `.harness/allowed_files.md` 与本 checklist。

## Plan Review Gate

- [x] Internal plan review：proposal/design/tasks/spec delta/test plan/Harness 边界。
- [x] Codex independent plan review：no blocking findings；clarify findings 已处理。
- [x] OpenCode independent plan review：已先运行 `opencode session list`，并复用 `ses_1018bd2aeffeKLTCcQhhuQ1jFZ`；no blocking findings；clarify findings 已处理。
- [x] 所有 plan findings 按 `fix / clarify / reject / defer` 分类并处理。
- [x] `openspec validate cleanup-control-routing-and-test-names --strict` 通过。
- [x] 停在 implementation confirmation gate；用户已确认继续小修正。

Plan findings:

- `clarify`（internal）：`HANDOFF_TO_NEXT_CHAT.md` 的 latest commit / merge-push state 属于本阶段文档状态修正范围；该修正不改变 runtime scope。
- `clarify`（OpenCode）：classifier extraction is routing-only；`_capability_status_answer()` and `_asks_about_unimplemented_v10_stack()` answer-selection behavior remains unchanged。
- `clarify`（OpenCode）：test naming cleanup must preserve existing route and answer assertions after rename。
- `clarify`（OpenCode）：`test_v6_kernel_does_not_expose_future_runtime_components` is in scope for capability-oriented rename because it asserts stable AgentLoop composition, not V6-only behavior。
- `clarify`（Codex）：long-term specs listed in proposal impact are archive-only paths, not implementation-edit paths。
- `clarify`（Codex）：capability-status classifier must remain inside `RequestRouter` and must not move ahead of AgentLoop pre-router routes。

## Implementation Gate（plan review 后）

- [x] RED tests：capability-status classifier 保持 route/keyword/reason，且不调用 repo RAG。
- [x] RED tests：包含 location/search 意图的问题不被 capability-status 吞掉。
- [x] RED tests：Assistant Control Surface parser 仍只接受明确状态触发词，不吞 capability-status、Memory 或 Long Task command。
- [x] Test naming cleanup：历史阶段命名测试改成能力导向命名，不削弱断言。
- [x] Runtime：`app/harness/kernel.py` 最小 helper/classifier 抽取，不改 public `/chat` contract。

Implementation evidence:

- RED focused test failed as expected because `CapabilityStatusClassifier` did not exist。
- GREEN focused classifier/parser tests：3 passed。
- Adjacent AgentLoop / Assistant Control Surface / Chat API tests：93 passed。
- Local ruff for changed runtime/tests：passed。

## Final Review / Verification（implementation 后）

- [x] Focused routing/parser tests：3 passed。
- [x] Adjacent `/chat` contract tests：`pytest tests/test_agent_harness_kernel.py tests/test_assistant_control_surface.py tests/test_chat_api.py -q` 为 93 passed。
- [x] `ruff check .`：passed。
- [x] `openspec validate --all`：23 passed，0 failed。
- [x] `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`：pytest 519 passed，1 skipped；ruff、stage docs scan、skill eval structure scan passed。
- [x] `git diff --check`：passed，仅 CRLF normalization warnings。
- [x] Final implementation review and finding triage。
- [x] Focused Stage Debt Sweep。
- [x] Archive readiness check。
- [x] OpenSpec archive completed。
- [x] Archive-after `openspec list`：No active changes found。
- [x] Archive-after `openspec validate --all`：22 passed，0 failed。
- [x] Archive-after full `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`：pytest 519 passed，1 skipped；ruff、stage docs scan、skill eval structure scan passed。

Final implementation review findings:

- `fix`（Codex）：`docs/PROGRESS.md` and `HANDOFF_TO_NEXT_CHAT.md` still described final verification as incomplete after full verification had passed；已补齐 current verification and final review status。
- `clarify`（Codex）：spec deltas described `capability/status intent` like an independent pre-router route；已澄清为 `RequestRouter` 内部 capability_status / repo_search / chat_only routing，且 classifier 不得 hoist 到 AgentLoop pre-router routes 之前。
- OpenCode final re-review：复用 `ses_1018bd2aeffeKLTCcQhhuQ1jFZ`；confirmed Codex findings closed；no findings。

Stage Debt Sweep:

- 覆盖 changed runtime/tests/docs/OpenSpec/Harness：`app/harness/kernel.py`、`tests/test_agent_harness_kernel.py`、`tests/test_assistant_control_surface.py`、active OpenSpec artifacts、`.harness/allowed_files.md`、`.harness/review_checklist.md`、`docs/PROGRESS.md`、`HANDOFF_TO_NEXT_CHAT.md`。
- 覆盖直接依赖：`app/assistant/control_surface.py` explicit status parser、`AgentLoop._run_inner()` pre-router order、`RequestRouter.route()` fallback boundary、`AgentLoopResult.to_agent_result()` public contract。
- 结论：未发现新增 blocking debt。`CapabilityStatusClassifier` remains inside `RequestRouter`；answer-selection behavior and Assistant Control Surface triggers remain unchanged；public `/chat` contract remains unchanged。

Archive readiness:

- Blocking findings closed；Codex final review findings 已处理；OpenCode final re-review no findings；focused/adjacent tests、OpenSpec all、ruff、full verify 和 `git diff --check` 已通过。最终文档/spec 修正后已重跑 `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`，结果仍为 pytest 519 passed，1 skipped；ruff、stage docs scan、skill eval structure scan passed。

Archive evidence:

- `openspec archive cleanup-control-routing-and-test-names --yes` succeeded；长期 `agent-loop-tool-execution` 和 `assistant-control-surface` specs 已同步；archive-after `openspec validate --all` 为 22 passed，0 failed。
- Archive-after full `scripts/verify.ps1` passed：pytest 519 passed，1 skipped；ruff、stage docs scan、skill eval structure scan passed。
