## 1. Planning And Harness

- [x] 1.1 Confirm branch, worktree, recent commits, remote sync, and active OpenSpec state.
- [x] 1.2 Read `AGENTS.md`, required project docs, OpenSpec README, Harness rules, and workflow/planning skills.
- [x] 1.3 Create proposal, design, tasks, and spec deltas.
- [x] 1.4 Synchronize `.harness/allowed_files.md` and `.harness/review_checklist.md`.
- [x] 1.5 Run internal plan review and classify findings as `fix`, `clarify`, `reject`, or `defer`.
- [x] 1.6 Run Codex independent plan review and classify findings as `fix`, `clarify`, `reject`, or `defer`.
- [x] 1.7 Run `opencode session list` and OpenCode independent plan review using session reuse rules; classify findings as `fix`, `clarify`, `reject`, or `defer`.
- [x] 1.8 Run `openspec validate cleanup-control-routing-and-test-names --strict`.

Plan findings:

- `clarify`（internal）：`HANDOFF_TO_NEXT_CHAT.md` 的 latest commit / merge-push state 属于本阶段文档状态修正范围；该修正不改变 runtime scope。
- `clarify`（OpenCode）：classifier extraction is routing-only；`_capability_status_answer()` and `_asks_about_unimplemented_v10_stack()` answer-selection behavior remains unchanged。
- `clarify`（OpenCode）：test naming cleanup must preserve existing route and answer assertions after rename。
- `clarify`（OpenCode）：`test_v6_kernel_does_not_expose_future_runtime_components` is in scope for capability-oriented rename because it asserts stable AgentLoop composition, not V6-only behavior。
- `clarify`（Codex）：long-term specs listed in proposal impact are archive-only paths, not implementation-edit paths。
- `clarify`（Codex）：capability-status classifier must remain inside `RequestRouter` and must not move ahead of AgentLoop pre-router routes。

## 2. Implementation After Approval

- [x] 2.1 Add RED tests proving capability-status classification stays route-only and does not swallow location/search questions.
- [x] 2.2 Add or retain RED tests proving Assistant Control Surface parser remains narrow and does not swallow capability-status, Memory, or Long Task commands.
- [x] 2.3 Rename historical-stage test names to stable capability names where behavior is not stage-specific, preserving existing assertions.
- [x] 2.4 Implement the smallest internal classifier/helper extraction in `app/harness/kernel.py`.
- [x] 2.5 Update `docs/PROGRESS.md` and `HANDOFF_TO_NEXT_CHAT.md` for resolved debt and true closeout state.

Implementation evidence:

- RED focused test failed as expected because `CapabilityStatusClassifier` did not exist.
- GREEN focused classifier/parser tests：3 passed。
- Adjacent AgentLoop / Assistant Control Surface / Chat API tests：93 passed。
- Local ruff for changed runtime/tests：passed。

## 3. Review, Verification, Archive

- [x] 3.1 Run focused routing/parser tests.
- [x] 3.2 Run adjacent `/chat` contract tests.
- [x] 3.3 Run `ruff check .`.
- [x] 3.4 Run `openspec validate --all`.
- [x] 3.5 Run full `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`.
- [x] 3.6 Run `git diff --check`.
- [x] 3.7 Run final implementation review and triage findings.
- [x] 3.8 Perform focused Stage Debt Sweep over changed runtime/tests/docs/specs/Harness and directly dependent paths.
- [x] 3.9 Archive the OpenSpec change only after blocking findings are closed and validation passes.

Verification evidence:

- Focused classifier/parser tests：3 passed。
- Adjacent `pytest tests/test_agent_harness_kernel.py tests/test_assistant_control_surface.py tests/test_chat_api.py -q`：93 passed。
- `ruff check .`：passed。
- `openspec validate --all`：23 passed，0 failed。
- Full `powershell -ExecutionPolicy Bypass -File scripts\verify.ps1`：pytest 519 passed，1 skipped；ruff、stage docs scan、skill eval structure scan passed。After final docs/spec review fixes, rerun full verification also passed with the same result.
- `git diff --check`：passed，仅 CRLF normalization warnings。

Final implementation review findings:

- `fix`（Codex）：`docs/PROGRESS.md` and `HANDOFF_TO_NEXT_CHAT.md` still described final verification as incomplete after full verification had passed；已补齐 current verification and final review status。
- `clarify`（Codex）：spec deltas described `capability/status intent` like an independent pre-router route；已澄清为 `RequestRouter` 内部 capability_status / repo_search / chat_only routing，且 classifier 不得 hoist 到 AgentLoop pre-router routes 之前。
- OpenCode final re-review：复用 `ses_1018bd2aeffeKLTCcQhhuQ1jFZ`；confirmed Codex findings closed；no findings。

Stage Debt Sweep:

- 覆盖 changed runtime/tests/docs/OpenSpec/Harness：`app/harness/kernel.py`、`tests/test_agent_harness_kernel.py`、`tests/test_assistant_control_surface.py`、active OpenSpec artifacts、`.harness/allowed_files.md`、`.harness/review_checklist.md`、`docs/PROGRESS.md`、`HANDOFF_TO_NEXT_CHAT.md`。
- 覆盖直接依赖：`app/assistant/control_surface.py` explicit status parser、`AgentLoop._run_inner()` pre-router order、`RequestRouter.route()` fallback boundary、`AgentLoopResult.to_agent_result()` public contract。
- 结论：未发现新增 blocking debt。`CapabilityStatusClassifier` remains inside `RequestRouter`；answer-selection behavior and Assistant Control Surface triggers remain unchanged；public `/chat` contract remains unchanged。
