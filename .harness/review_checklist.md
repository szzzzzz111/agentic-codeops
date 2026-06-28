# 当前 Review 清单

Active OpenSpec change：无。
最近归档 OpenSpec change：`harden-git-metadata-output-bounds`。
风险级别：high。

目标是修复 shared Git metadata runner 的输出上限执行时机：stdout 超过
`MAX_GIT_METADATA_BYTES` 时必须在内容被保留/解码/暴露前 fail closed，并 kill/reap Git 进程。

## Planning / Harness

- [x] 已读取 `AGENTS.md`、必读文档、OpenSpec README、Harness rules、workflow/review skills。
- [x] 已检查 branch、worktree、recent commits、remote sync 和 active OpenSpec changes。
- [x] 已选择代码债：`app/worktrees/git_metadata.py` shared metadata stdout output-bound hardening。
- [x] 已创建 OpenSpec proposal、design、tasks、spec deltas。
- [x] 已同步 `.harness/allowed_files.md` 与本 checklist。

## Plan Review Gate

- [x] Internal plan review：proposal/design/tasks/spec deltas/test plan/Harness 边界；发现 spec oversize 场景把“读取 1 个额外字节用于检测”与“保留/解码/暴露 cap 外内容”混淆，已按 `clarify` 修正。
- [x] Codex independent plan review：发现 shared runner 影响范围漏列 re-verification / promotion（`fix`）、oversize RED 测试不足以证明旧 temp-file 实现失败（`fix`）、disposal postcheck metadata failure 语义需明确（`clarify/fix`）；已补 spec deltas、proposal/design/tasks/test plan。
- [x] OpenCode independent plan review：已先运行 `opencode session list` 并复用已有 session；终端初次超时后检查 session/final text，最终 finding 为 bounded reap 常量未明确（`clarify`）、cap-edge RED 断言需精确（`clarify`）、spec delta caller 覆盖需补齐（`clarify`）；已补 `GIT_METADATA_REAP_TIMEOUT_SECONDS = 1.0`、cap-edge 测试要求、re-verification / promotion spec deltas。
- [x] 所有 plan findings 按 `fix / clarify / reject / defer` 分类并处理。
- [x] `openspec validate harden-git-metadata-output-bounds --strict` 通过。
- [x] Planning artifact 复核：`openspec validate --all` 23 passed；`git diff --check` 无 whitespace error（仅 Windows 换行提示）。
- [x] 已停在 implementation confirmation gate，等待用户明确批准。

## Implementation Gate（用户确认后）

- [x] RED tests：metadata timeout kills/reaps and returns `None`。
- [x] RED tests：stdout oversize kills/reaps and returns `None` without retaining oversize bytes。
- [x] RED tests：stdout read failure or reader non-completion returns `None`。
- [x] Regression：non-zero exit returns `None`。
- [x] Runtime：`git_metadata.py` 使用 bounded stdout pipe reader，保留 fixed argv、`shell=False`、`GIT_OPTIONAL_LOCKS=0`、stderr discard、no retry、no repair。
- [x] Preserve：inspection/disposal/reverification/promotion preflight callers 继续把 metadata unavailable 映射为现有 safe failure/partial 语义。

## Final Review / Verification（implementation 后）

- [x] Focused `pytest tests/test_worktree_disposal.py -q`：38 passed。
- [x] Adjacent worktree inspection/reverification/promotion/disposal regressions：inspection 20 passed；reverification 31 passed；promotion 28 passed；disposal 37 passed。
- [x] `ruff check .`：passed。
- [x] `openspec validate --all`：23 passed，0 failed。
- [x] `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`：pytest 499 passed，1 skipped；ruff、stage docs scan、skill eval structure scan passed。
- [x] `git diff --check`：无 whitespace error，仅 CRLF normalization warnings。
- [x] Final implementation review and finding triage：internal review 无 P0/P1/P2；OpenCode final review 复用 `ses_1018bd2aeffeKLTCcQhhuQ1jFZ`，无 P0/P1/P2。P3 start-failure coverage 按 `fix` 补测试，P3 reader thread name 按 `clarify/fix` 增加 `name="git-metadata-reader"`；focused re-review 确认 P3 closed 且无新 P0/P1/P2。
- [x] Focused Stage Debt Sweep：覆盖 changed runtime/tests/docs/OpenSpec/Harness 和直接依赖的 inspection、disposal/reconciliation、re-verification、promotion metadata caller；无 blocking debt。残余相邻债为 `app/worktrees/disposal.py::_run_mutation()` destructive subprocess output cap，defer 到独立阶段。
- [x] Archive readiness check：blocking findings closed；tasks complete；`openspec validate --all` 23 passed；full `scripts/verify.ps1` passed；`git diff --check` passed with CRLF warnings only。

## Archive / Closeout

- [x] `openspec archive harden-git-metadata-output-bounds --yes` 成功，归档到 `openspec/changes/archive/2026-06-28-harden-git-metadata-output-bounds/`，并同步 4 个长期 specs。
- [x] Archive 后 `openspec list`：No active changes found。
- [x] Archive 后 `openspec validate --all`：22 passed，0 failed。
- [x] Archive 后 full `scripts/verify.ps1`：pytest 499 passed，1 skipped；ruff、stage docs scan、skill eval structure scan passed。
- [x] Fast-forward merge 到 `main` 并推送到 `agentic-codeops/main`。
- [x] Merge 后 full `scripts/verify.ps1`：pytest 499 passed，1 skipped；ruff、stage docs scan、skill eval structure scan passed。
