# 交接给下一轮 Chat

## 当前基线

- 当前分支：`main`。
- Active OpenSpec change：无；`openspec list` 为 No active changes found。
- 最近归档 OpenSpec change：`cleanup-control-routing-and-test-names`，归档到
  `openspec/changes/archive/2026-07-03-cleanup-control-routing-and-test-names/`。
- 最近已完成 implementation commit：`b3c92f5 Clean up control routing classifier`，已 fast-forward
  合并到 `main`；closeout 文档随当前 `main` 一起推送。
- 当前阶段风险级别：medium。
- 当前阶段目标：清理 control routing（控制路由）和 test naming（测试命名）小代码债，不扩展
  Assistant Control Surface 自然语言触发词，不改变 `/chat` public contract。

继续前先刷新 live state：

```powershell
git status --short --branch
git log -5 --oneline --decorate
openspec list
openspec validate --all
```

## 已完成内容

- Planning gate 已完成并记录在 `.harness/review_checklist.md`：internal、Codex independent
  和 OpenCode independent plan review 均完成，plan findings 已按 `clarify` triage。
- `openspec validate cleanup-control-routing-and-test-names --strict` 已通过。
- TDD RED 已完成：`CapabilityStatusClassifier` import 在旧实现下按预期失败。
- GREEN 实现已完成：capability-status classifier/helper 已抽出并留在 `RequestRouter` 内；
  `_capability_status_answer()` answer-selection 行为不变；Assistant Control Surface parser 未扩展。

## 当前验证

- RED：focused classifier test 在旧实现下 import failed，因为 `CapabilityStatusClassifier` 不存在。
- GREEN focused：classifier/parser tests 3 passed。
- Adjacent：`pytest tests/test_agent_harness_kernel.py tests/test_assistant_control_surface.py tests/test_chat_api.py -q`：93 passed。
- `ruff check .`：passed。
- `openspec validate --all`：23 passed，0 failed。
- Full `powershell -ExecutionPolicy Bypass -File scripts\verify.ps1`：pytest 519 passed、1 skipped；
  ruff、stage docs scan、skill eval structure scan 均通过。
- `git diff --check`：passed，仅 CRLF normalization warnings。
- Archive-after `openspec validate --all`：22 passed，0 failed。
- `openspec archive cleanup-control-routing-and-test-names --yes` 已成功，长期
  `agent-loop-tool-execution` 和 `assistant-control-surface` specs 已同步。
- Archive-after full `powershell -ExecutionPolicy Bypass -File scripts\verify.ps1`：pytest 519 passed、
  1 skipped；ruff、stage docs scan、skill eval structure scan 均通过。
- Codex final review：documentation backfill finding 和 spec wording finding 已按 `fix` / `clarify`
  处理；OpenCode final re-review 复用 `ses_1018bd2aeffeKLTCcQhhuQ1jFZ`，confirmed findings closed，
  no findings。
- Focused Stage Debt Sweep：覆盖 changed runtime/tests/docs/OpenSpec/Harness 与
  `app/assistant/control_surface.py`、`AgentLoop._run_inner()`、`RequestRouter.route()`、
  `AgentLoopResult.to_agent_result()` 直接边界，未发现新增 blocking debt。

## 下一步

- 当前无 active OpenSpec change。后续如启动新阶段，先创建新的 OpenSpec change 并同步 Harness。

## 剩余债

- 本阶段已处理 `docs/PROGRESS.md` 记录的 control routing / test naming 小代码债。
- Final review 与 Focused Stage Debt Sweep 未发现新增 blocking debt。
