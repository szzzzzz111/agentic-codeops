# 当前 Review 清单

Active OpenSpec change：无。
最近归档 OpenSpec change：`omit-empty-evidence-snippets`，归档到
`openspec/changes/archive/2026-07-02-omit-empty-evidence-snippets/`。
风险级别：medium。

目标是修复 `app/rag/evidence.py::build_evidence_pack()` 对 empty / whitespace-only
snippet 的 Context Budget 计数：空 snippet 保留 evidence item 以便审计，但不得计入
`included_count`，不得消耗 budget，不得标记 truncated，应计入 `omitted_count`。

## Planning / Harness

- [x] 已读取 `AGENTS.md`、必读文档、OpenSpec README、Harness rules、workflow/planning skills。
- [x] 已检查 branch、worktree、recent commits、remote sync 和 active OpenSpec changes。
- [x] 已选择代码债：`app/rag/evidence.py` empty snippet included-count 语义。
- [x] 已创建 OpenSpec proposal、design、tasks、spec delta。
- [x] 已同步 `.harness/allowed_files.md` 与本 checklist。

## Plan Review Gate

- [x] Internal plan review：proposal/design/tasks/spec delta/test plan/Harness 边界。Finding：`clarify`，confirmed scope is limited to Evidence Pack budget accounting and must not alter grounded answer assembly or `/chat` contract.
- [x] Codex independent plan review：Codex subagent `019f1d92-6e25-7370-bbf4-dd010e1313f9` 只读 review，no blocking findings。
- [x] OpenCode independent plan review：已先运行 `opencode session list`，并复用 `ses_1018bd2aeffeKLTCcQhhuQ1jFZ`，no blocking findings。
- [x] 所有 plan findings 按 `fix / clarify / reject / defer` 分类并处理。
- [x] `openspec validate omit-empty-evidence-snippets --strict` 通过。
- [x] 停在 implementation confirmation gate；用户已确认继续完成代码债。

Plan findings:

- `clarify`（internal）：scope is limited to Evidence Pack budget accounting; do not alter grounded answer assembly or `/chat` contract.
- `clarify`（Codex）：mixed ordering should be covered so an empty snippet before a non-empty snippet does not consume budget or prevent later inclusion；已补入 RED test plan。
- `clarify`（OpenCode）：evidence id wording could imply use of the budget-assigned `EvidenceItem.snippet`；已澄清为 original stripped snippet before budget assignment。
- `clarify`（OpenCode）：in-budget scenario needed a no-empty-snippet precondition for `omitted_count == 0`；已补 spec delta。
- `clarify`（OpenCode）：current behavior is inconsistent across `remaining > 0` and `remaining == 0`；已补 design context。

## Implementation Gate（用户确认后）

- [x] RED tests：empty snippet 保留 item 但 `included=False`、`truncated=False`、`omitted_count+1`、budget used 不增加。
- [x] RED tests：whitespace-only snippet 经 normalization 后同样 omitted。
- [x] Regression：非空 include / truncate / omit 语义保持不变。
- [x] Runtime：`build_evidence_pack()` 最小修改，不改 retrieval、grounded answer、provider 或 `/chat` contract。

## Final Review / Verification（implementation 后）

- [x] Focused `pytest tests/test_evidence_pack.py -q`：7 passed。
- [x] Adjacent RAG / grounded answer contract tests：`pytest tests/test_grounded_answer.py tests/test_chat_api.py tests/test_repo_rag.py -q` 为 43 passed。
- [x] `ruff check .`：passed。
- [x] `openspec validate --all`：23 passed，0 failed。
- [x] `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`：pytest 513 passed，1 skipped；ruff、stage docs scan、skill eval structure scan passed。
- [x] `git diff --check`：passed，仅 CRLF normalization warnings。
- [x] Final implementation review and finding triage。
- [x] Focused Stage Debt Sweep。
- [x] Archive readiness check。

Final implementation review findings:

- `fix`（Codex P3）：final verification / archive gate evidence had not yet been backfilled in tasks and checklist；已补齐 focused/adjacent/full verification、final review、debt sweep 和 archive readiness 记录。
- OpenCode final implementation review：no `fix` / `clarify` / `reject` / `defer` findings；no blocking findings。

Stage Debt Sweep:

- 覆盖 changed runtime/tests/docs/OpenSpec/Harness：`app/rag/evidence.py`、`tests/test_evidence_pack.py`、active OpenSpec artifacts、`.harness/allowed_files.md`、`.harness/review_checklist.md`、`docs/PROGRESS.md`、`HANDOFF_TO_NEXT_CHAT.md`。
- 覆盖直接依赖：`app/answering/grounded_answer.py`、`app/tools/tool_executor.py`、`app/harness/kernel.py`。
- 结论：未发现新增 blocking debt。Grounded answer 和 citation validation 仍只消费 `item.included and item.snippet`；public `/chat` contract、provider runtime、retriever behavior、CI 和网络依赖均未改变。

Archive readiness:

- Blocking findings closed；所有 implementation review findings 已 triage；focused/adjacent tests、OpenSpec strict/all、ruff、full verify 和 `git diff --check` 已通过。可进入 archive。

## Archive / Closeout

- [x] `openspec archive omit-empty-evidence-snippets --yes` 成功，归档到 `openspec/changes/archive/2026-07-02-omit-empty-evidence-snippets/`，并同步 `openspec/specs/repo-query-understanding-rag/spec.md`。
- [x] Archive 后 `openspec list`：No active changes found。
- [x] Archive 后 `openspec validate --all`：22 passed，0 failed。
- [x] Archive 后 full `scripts/verify.ps1`：pytest 513 passed，1 skipped；ruff、stage docs scan、skill eval structure scan passed。
- [x] Archive 后 `git diff --check`：passed，仅 CRLF normalization warnings。
