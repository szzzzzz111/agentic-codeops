# 交接给下一轮 Chat

## 当前基线（2026-06-25）

- 当前集成分支：`main`。
- Active OpenSpec change：无。
- 最近完成阶段：V24 `polish-demo-cli-capability-surface`，已归档到
  `openspec/changes/archive/2026-06-25-polish-demo-cli-capability-surface/` 并 fast-forward 合入
  `main`。
- 阶段目标已完成：CLI Capability Surface / Demo-ready Product Surface，以及计划级 review
  workflow hardening。
- 原 Verified Patch Promotion 已顺延为 V25/backlog 候选；当前 runtime 仍不实现 promotion、
  commit/merge/push automation、branch management、PR creation、后台任务、runtime subagents 或 connectors。

## 已完成能力

- `repopilot patch "<request>"` 固定映射为 `create patch: <request>`，不依赖用户文案是否出现
  “patch”。
- CLI patch id validator 固定为 `^patch_[A-Za-z0-9_]{1,122}$`。
- CLI 输出为 `Trace`、`Answer`、`Related files`、`Tool calls` 分段，且只基于公开
  `trace_id`、`answer`、`related_files`、`tool_calls`。
- Workflow skills 已要求 medium/high 阶段实现前完成 internal plan review、Codex independent plan
  review、OpenCode independent plan review，并将外部 plan findings 按
  `fix / clarify / reject / defer` triage。
- OpenCode review 规则已写入：优先 `opencode session list`，再
  `opencode run --session <session_id> ...`；终端超时后先检查 session final assistant review
  text，不能直接算失败或通过。

## 验证与 Review

- `pytest tests/test_cli.py -q` -> 41 passed。
- `pytest tests/test_cli.py tests/test_chat_api.py tests/test_agent_harness_kernel.py tests/test_verification_runner.py -q`
  -> 133 passed。
- `openspec validate --all` -> archive 后 20 passed，0 failed。
- Full `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1` -> 441 passed、1 skipped；
  ruff、stage docs scan、skill eval structure scan passed。
- `git diff --check` -> passed；仅有 CRLF normalization warnings。
- Final implementation review：internal review 修复两处 wording drift；OpenCode focused external review
  复用 session `ses_1018bd2aeffeKLTCcQhhuQ1jFZ`，终端超时后从 final assistant review text 取证，
  无 P0/P1，findings 已 triage。

## 下一步

开始新阶段前先查询 live state：

```powershell
git status --short --branch
git log -5 --oneline --decorate
openspec list
openspec validate --all
```

下一阶段如继续推进 Verified Patch Promotion，必须新建独立 OpenSpec change，并重新同步
`.harness/allowed_files.md` 与 `.harness/review_checklist.md`；不要把 V25/backlog 候选写成当前已实现能力。
