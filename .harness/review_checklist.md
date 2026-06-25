# 当前 Review 清单

当前无 active OpenSpec change。最近归档 change：`add-demo-ready-agent-cli`。

## Planning gate

- [x] 当前分支已切到 `codex/add-demo-ready-agent-cli`。
- [x] 起始 `main` 工作树干净，最近提交为 `dcf95c2 Polish README facade and archive CLI planning`。
- [x] 起始 `openspec list` 为 No active changes found。
- [x] 风险级别判定为 `medium`：新增用户命令入口，但不改公开 API、provider、CI、Git/promotion 或持久化模型。
- [x] 已创建 OpenSpec artifacts 和 spec deltas。
- [x] 已同步 `.harness/allowed_files.md`，实现前只开放 CLI runtime、package metadata、CLI tests、相关 docs/specs/harness。
- [x] `openspec validate add-demo-ready-agent-cli --strict` 通过。
- [x] `openspec validate --all` 通过：21 passed，0 failed。
- [x] `git diff --check` 通过；仅有 CRLF normalization warning。
- [x] 完成内部 plan review：proposal、design、tasks、spec deltas、test plan、Harness 边界互相一致。
- [x] 已获得用户确认后进入 runtime/tests；实现按 TDD RED -> GREEN 完成。

## CLI implementation review target

- [x] `repopilot` console entrypoint 只调用现有 `ChatService.handle_chat()`，不重写 AgentLoop。
- [x] `ask`、`patch`、`patch confirm`、`patch confirm --verify`、`verify`、`status`、`audit latest` 映射到现有 chat semantics。
- [x] `verify` label 只允许 `verify`、`pytest`、`ruff`。
- [x] empty required values、unsafe patch id、shell-like syntax、管道、重定向、环境变量赋值、extra args 在调用 `ChatService` 前拒绝。
- [x] CLI 不新增网络依赖，不读取 provider key，不修改 live eval 或默认 Patch wiring。
- [x] CLI 不实现 V24 promotion、commit、merge、push、branch management 或 PR creation。
- [x] CLI 输出只包含安全摘要：`trace_id`、`answer`、`related_files`、`tool_calls`。
- [x] Usage/validation error exit code 为 `2`；unexpected wrapper failure 为 `1`；正常 ChatService response 为 `0`。
- [x] README 不再说 CLI 尚未实现，但明确它是薄入口，不扩大 runtime 能力。

## Verification evidence

- [x] Focused CLI tests pass：`pytest tests/test_cli.py -q` -> 32 passed。
- [x] Adjacent AgentLoop/API/verification tests pass：`pytest tests/test_cli.py tests/test_chat_api.py tests/test_agent_harness_kernel.py tests/test_verification_runner.py -q` -> 124 passed。
- [x] `openspec validate add-demo-ready-agent-cli --strict` pass。
- [x] `openspec validate --all` pass：21 passed，0 failed。
- [x] Pre-archive `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1` pass：432 passed，1 skipped；ruff and stage scans pass。
- [x] `git diff --check` pass；仅有 CRLF normalization warning。
- [x] Archive-after `openspec validate --all` pass：20 passed，0 failed。
- [x] Archive-after `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1` pass：432 passed，1 skipped；ruff and stage scans pass。
- [x] Archive-after `git diff --check` pass；仅有 CRLF normalization warning。

## Final review evidence

- [x] Internal final review completed after latest runtime/test/doc changes：no P0/P1/P2 findings. Inspected CLI delegation, parser fail-closed behavior, output summary, README claims, feature list, package script, tests, and OpenSpec task state.
- [x] Focused external review completed via reused OpenCode session `ses_10290b071ffeLx5JxfppaZ3qfo`. Result: no P0/P1/P2 blockers. Non-blocking empty-value exit-code observation was fixed with RED coverage; focused CLI tests now pass at 32 cases and adjacent regressions now pass at 124 cases.
- [x] Stage Debt Sweep completed for `app/cli.py`, `tests/test_cli.py`, `pyproject.toml`, README/FEATURE_LIST/PROGRESS/HANDOFF, and OpenSpec tasks. No new blocking debt found; residual risk is that CLI intentionally supports only one quoted argument for `ask` and `patch` free text in this first demo-ready slice.
- [x] OpenSpec archive completed：`add-demo-ready-agent-cli` archived as `openspec/changes/archive/2026-06-25-add-demo-ready-agent-cli/` and long-term specs updated.
