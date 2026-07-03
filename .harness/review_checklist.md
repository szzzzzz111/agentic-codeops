# 当前 Review 清单

Active OpenSpec change：无。
最近归档 OpenSpec change：`parameterize-hybrid-fusion-settings`，归档到
`openspec/changes/archive/2026-07-03-parameterize-hybrid-fusion-settings/`。
风险级别：medium。

目标是修复 `app/rag/repo_rag.py` 中 hybrid fusion settings（混合检索打分配方）
硬编码债：lexical / embedding 权重和 `min_fused_score` 必须成为显式、可校验、
可审计的 deterministic settings；默认排序行为、lexical anchor、公开 `/chat` contract 均保持不变。

## Planning / Harness

- [x] 已读取 `AGENTS.md`、必读文档、OpenSpec README、Harness rules、workflow/planning skills。
- [x] 已检查 branch、worktree、recent commits、remote sync 和 active OpenSpec changes。
- [x] 已选择代码债：`app/rag/repo_rag.py` hybrid fusion weights / threshold 硬编码语义。
- [x] 已创建 OpenSpec proposal、design、tasks、spec delta。
- [x] 已同步 `.harness/allowed_files.md` 与本 checklist。

## Plan Review Gate

- [x] Internal plan review：proposal/design/tasks/spec delta/test plan/Harness 边界。Finding：`fix`，test plan threshold wording corrected from "higher threshold passes" to deterministic pass/filter behavior.
- [x] Codex independent plan review：Codex subagent `019f2584-652b-7920-88f1-7c1ca2e95cec` 只读 review，no blocking findings after scope fix。
- [x] OpenCode independent plan review：已先运行 `opencode session list`，并复用 `ses_1018bd2aeffeKLTCcQhhuQ1jFZ`，no blocking findings。
- [x] 所有 plan findings 按 `fix / clarify / reject / defer` 分类并处理。
- [x] `openspec validate parameterize-hybrid-fusion-settings --strict` 通过。
- [x] 停在 implementation confirmation gate；用户已确认继续推进代码债。

Plan findings:

- `fix`（internal）：test plan threshold wording corrected from "higher threshold passes" to deterministic pass/filter behavior。
- `clarify`（OpenCode）：settings must be the single source of truth when provided；standalone compatibility kwargs apply only when `settings` is omitted，已补 design。
- `clarify`（OpenCode）：`max_results` remains a per-call cap rather than a fusion settings field，已补 design。
- `clarify`（OpenCode）：settings validation is construction-time fail fast，已补 design。
- `fix`（Codex）：allowed files were too narrow to fulfill internal audit/trace contract；已扩大 scope 到 `app/tools/tool_executor.py` 和 `tests/test_tool_executor.py`，并补 audit pass-through 测试计划。
- `clarify`（Codex）：OpenCode findings 已记录但 gate 仍 pending；已同步 gate 状态。

## Implementation Gate（用户确认后）

- [x] RED tests：默认 settings 保持当前 hybrid fusion score 和稳定排序。
- [x] RED tests：custom settings 可确定性改变 fusion mix / threshold，并记录 retriever audit summary。
- [x] RED tests：ToolExecutor 内部 audit summary 透传 effective settings，但 public `call_summary()` 不暴露。
- [x] RED tests：negative、non-finite、all-zero weights 等 invalid settings fail fast。
- [x] Regression：lexical anchor 与 public `/chat` contract 不改变。
- [x] Runtime：`HybridFusionSettings` 最小实现，不改 query understanding、rewrite、rerank、Evidence Pack、grounded answer、provider 或 `/chat` contract。

## Final Review / Verification（implementation 后）

- [x] Focused/adjacent `pytest tests/test_repo_rag.py tests/test_tool_executor.py tests/test_agent_harness_kernel.py tests/test_chat_api.py -q`：100 passed。
- [x] `ruff check .`：passed。
- [x] `openspec validate --all`：23 passed，0 failed。
- [x] `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`：pytest 517 passed，1 skipped；ruff、stage docs scan、skill eval structure scan passed。
- [x] `git diff --check`：passed，仅 CRLF normalization warnings。
- [x] Final implementation review and finding triage。
- [x] Focused Stage Debt Sweep。
- [x] Archive readiness check。

Final implementation review findings:

- `fix`（Codex）：final verification / review checklist / progress / handoff status had not yet been backfilled after implementation verification；已补齐。
- OpenCode final implementation review：no `fix` / `clarify` / `reject` / `defer` findings；no blocking findings。
- `fix`（Stage Debt Sweep）：`ToolExecutor` 不应在 retriever 未提供 fusion settings 时合成默认 audit values；已改为仅复制明确提供的 effective settings，并补 `tests/test_tool_executor.py` regression。
- `fix`（Stage Debt Sweep）：AgentLoop internal trace regression 只覆盖 `min_fused_score`，未覆盖新增 `lexical_weight` / `embedding_weight`；已补 `tests/test_agent_harness_kernel.py` adjacent regression，并同步 allowed files。

Stage Debt Sweep:

- 覆盖 changed runtime/tests/docs/OpenSpec/Harness：`app/rag/repo_rag.py`、`app/tools/tool_executor.py`、`tests/test_repo_rag.py`、`tests/test_tool_executor.py`、active OpenSpec artifacts、`.harness/allowed_files.md`、`.harness/review_checklist.md`、`docs/PROGRESS.md`、`HANDOFF_TO_NEXT_CHAT.md`。
- 覆盖直接依赖：`app/harness/kernel.py` 的 public `call_summary()` 和 internal trace/audit summary 路径。
- 结论：Stage Debt Sweep 的两个 `fix` findings 已关闭。新增 settings 仅进入内部审计摘要，不进入 public `call_summary()` 或 `/chat` 顶层 contract；缺失 settings 时不会合成虚假的默认 audit values。

Archive readiness:

- Blocking findings closed；Codex/OpenCode fix verification 均 no findings；focused/adjacent tests、OpenSpec all、ruff、full verify 和 `git diff --check` 已通过。可进入 archive。

## Archive / Closeout

- [x] `openspec archive parameterize-hybrid-fusion-settings --yes` 成功，归档到 `openspec/changes/archive/2026-07-03-parameterize-hybrid-fusion-settings/`，并同步 `openspec/specs/repo-query-understanding-rag/spec.md`。
- [x] Archive 后 `openspec validate --all`：22 passed，0 failed。
- [x] Archive 后 full `scripts/verify.ps1`：pytest 517 passed，1 skipped；ruff、stage docs scan、skill eval structure scan passed。
- [x] Archive 后 `git diff --check`：passed，仅 CRLF normalization warnings。
