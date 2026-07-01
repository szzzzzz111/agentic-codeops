# 当前 Review 清单

Active OpenSpec change：无。
最近归档 OpenSpec change：`harden-worktree-disposal-mutation-output-bounds`，归档到
`openspec/changes/archive/2026-07-01-harden-worktree-disposal-mutation-output-bounds/`。
风险级别：high。

目标是修复 `app/worktrees/disposal.py::_run_mutation()` 的 destructive Git mutation
subprocess 输出上限执行时机：stdout/stderr 超过
`WORKTREE_DISPOSAL_MUTATION_OUTPUT_MAX_BYTES` 时必须在内容被保留/解码/暴露前 fail
closed，并 kill/reap Git 进程。

## Planning / Harness

- [x] 已读取 `AGENTS.md`、必读文档、OpenSpec README、Harness rules、workflow/review skills。
- [x] 已检查 branch、worktree、recent commits、remote sync 和 active OpenSpec changes。
- [x] 已选择代码债：`app/worktrees/disposal.py::_run_mutation()` destructive mutation output-bound hardening。
- [x] 已创建 OpenSpec proposal、design、tasks、spec delta。
- [x] 已同步 `.harness/allowed_files.md` 与本 checklist。

## Plan Review Gate

- [x] Internal plan review：proposal/design/tasks/spec delta/test plan/Harness 边界。
- [x] Codex independent plan review：`codex` CLI 不可执行后，已按用户授权使用 Codex subagent `019f1cff-87c5-79d3-9db2-c111f11e7a15` 完成只读 review。
- [x] OpenCode independent plan review：已先运行 `opencode session list`，并复用 `ses_1018bd2aeffeKLTCcQhhuQ1jFZ`。
- [x] 所有 plan findings 按 `fix / clarify / reject / defer` 分类并处理。
- [x] `openspec validate harden-worktree-disposal-mutation-output-bounds --strict` 通过。
- [x] 停在 implementation confirmation gate，等待用户明确批准。

Plan findings:

- `fix`：proposal/design 原先把 `process start failure` 写入 kill/reap 触发项；已改为“启动失败安全失败，已启动进程才 kill/reap”，避免 contract 要求不可执行行为。
- `clarify`（OpenCode P3-1）：design 未明确 safe mutation failure 的异常类型；已补充必须落入现有 caller 捕获边界，优先使用 `subprocess.SubprocessError`。
- `fix`（Codex P2）：测试计划未显式覆盖 mutation failure raw output / exception / path / traceback-like 泄漏；已新增覆盖 `WorktreeDisposalResult.public_summary`、AgentLoop public output 与 worktree disposal audit records 的 regression。
- `clarify`（Codex P3）：spec delta 对 process-start failure 与 non-zero exit 的 kill/reap 语义混在一起；已澄清 start failure 无需不存在的 process cleanup，已启动进程失败才 kill/reap 或 bounded-reap。
- `clarify`（Codex P3）：Codex review gate 仍未记录完成；已记录用户授权 subagent review 及处理结果。

Validation:

- `openspec validate harden-worktree-disposal-mutation-output-bounds --strict`：passed。
- `openspec validate --all`：23 passed, 0 failed。

Codex independent review status:

- `clarify`：`codex --help` 在沙箱与提升执行下均返回 `Access is denied`；命令解析到 WindowsApps packaged Codex executable。用户已授权使用 Codex subagent 作为替代审阅通道，该 gate 已完成。

## Implementation Gate（用户确认后）

- [x] RED tests：mutation timeout kills/reaps and returns safe mutation failure。
- [x] RED tests：stdout/stderr oversize kills/reaps without retaining or exposing raw output。
- [x] RED tests：stdout/stderr read failure or reader non-completion returns safe mutation failure。
- [x] Regression：process start failure and non-zero exit return safe mutation failure。
- [x] Regression：mutation failure preserves current disposal lifecycle semantics。
- [x] Runtime：`disposal.py::_run_mutation()` 使用 bounded stdout/stderr pipe runner，保留 fixed argv、`shell=False`、`GIT_OPTIONAL_LOCKS=0`、command order、no retry、no repair。
- [x] Preserve：preflight、postcheck、audit、scope、patch/worktree lifecycle 语义不变。

## Final Review / Verification（implementation 后）

- [x] Focused `pytest tests/test_worktree_disposal.py -q`：49 passed。
- [x] Adjacent worktree disposal/reconciliation and repo mutation locking regressions：`tests/test_repo_mutation_locking.py` 17 passed；`tests/test_worktree_disposal.py` 49 passed。
- [x] `ruff check .`：passed。
- [x] `openspec validate --all`：23 passed, 0 failed。
- [x] `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`：pytest 510 passed, 1 skipped；ruff、stage docs scan、skill eval structure scan passed。
- [x] `git diff --check`：passed，仅 CRLF normalization warnings。
- [x] Final implementation review and finding triage。
- [x] Focused Stage Debt Sweep。
- [x] Archive readiness check。

Final implementation review findings:

- `fix`（Codex P2）：reader 线程遇到非 `OSError`/`ValueError` 的普通异常时会 fail open；已补 unexpected pipe exception RED regression，并让 `_read_mutation_output()` 对普通 `Exception` fail closed，仅设置 `state.failed`，不暴露异常文本。
- `fix`（Codex P2 / OpenCode P3）：reader non-completion 已在 checklist/tasks 中声明但缺少 focused coverage；已补 `reader_incomplete` regression。
- `fix`（Codex P2）：泄漏回归未直接覆盖 `WorktreeDisposalResult.public_summary`；已补 direct `public_summary` regression。
- `clarify`（Codex P3）：`docs/PROGRESS.md` “最多读取”措辞不精确；已改为最多计数/保留 cap，允许读取 1 byte sentinel 但不保留/解码/暴露。
- `clarify`（OpenCode P3）：`_mutation_failure_reason()` 同时遇到 stdout/stderr failure 时只返回首个 stream reason；public/lifecycle 仍统一为 `mutation_failed`，该内部诊断选择不影响 fail-closed 语义。
- `defer`（OpenCode P3）：`_kill_and_reap_mutation()` kill/wait 自身异常吞掉路径未单独测试；这是 best-effort cleanup 的防御分支，当前 timeout/oversize/read/non-completion regressions 已覆盖调用该 cleanup 的主要行为。

Stage Debt Sweep:

- 覆盖 changed runtime/tests/docs/OpenSpec/Harness：`app/worktrees/disposal.py`、`tests/test_worktree_disposal.py`、`docs/PROGRESS.md`、`HANDOFF_TO_NEXT_CHAT.md`、`.harness/allowed_files.md`、`.harness/review_checklist.md`、active OpenSpec artifacts。
- 覆盖直接依赖：`app/worktrees/manager.py`、`app/tools/tool_executor.py`、`app/audit/manager.py`、`app/harness/kernel.py`。
- 结论：未发现新增 blocking debt。`capture_output=True` 命中仅存在于测试 helper 或“已替换旧实现”的文档语境；敏感字符串命中仅存在于泄漏回归测试断言；未发现 public `/chat`、preflight/postcheck、repo lock、ToolExecutor、PermissionPolicy、ApprovalGate 或 promotion scope drift。

Archive readiness:

- Blocking findings closed；all implementation review findings triaged；OpenSpec strict/all、focused tests、full verify、ruff 和 `git diff --check` 已通过。可进入 OpenSpec archive。

## Archive / Closeout

- [x] `openspec archive harden-worktree-disposal-mutation-output-bounds --yes` 成功，归档到 `openspec/changes/archive/2026-07-01-harden-worktree-disposal-mutation-output-bounds/`，并同步 `openspec/specs/worktree-disposal-reconciliation/spec.md`。
- [x] Archive 后 `openspec list`：No active changes found。
- [x] Archive 后 `openspec validate --all`：22 passed, 0 failed。
- [x] Archive 后 full `scripts/verify.ps1`：pytest 510 passed, 1 skipped；ruff、stage docs scan、skill eval structure scan passed。
- [x] Archive 后 `git diff --check`：passed，仅 CRLF normalization warnings。
- [x] Implementation commit `6c3ae95` 已 fast-forward 合入 `main`。
- [x] Merge 后 full `scripts/verify.ps1`：pytest 510 passed, 1 skipped；ruff、stage docs scan、skill eval structure scan passed。
- [x] Push 到 `agentic-codeops/main`。
