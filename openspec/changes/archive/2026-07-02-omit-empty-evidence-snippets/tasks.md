## 1. Planning And Harness

- [x] 1.1 Confirm branch, worktree, recent commits, remote sync, and active OpenSpec state.
- [x] 1.2 Read `AGENTS.md`, required project docs, OpenSpec README, Harness rules, and workflow/planning skills.
- [x] 1.3 Select the next small code debt: empty Evidence Pack snippets should not count as included evidence.
- [x] 1.4 Create proposal, design, tasks, and spec delta.
- [x] 1.5 Synchronize `.harness/allowed_files.md` and `.harness/review_checklist.md`.
- [x] 1.6 Run internal plan review and classify findings as `fix`, `clarify`, `reject`, or `defer`.
- [x] 1.7 Run Codex independent plan review and classify findings as `fix`, `clarify`, `reject`, or `defer`.
- [x] 1.8 Run `opencode session list` and OpenCode independent plan review using session reuse rules; classify findings as `fix`, `clarify`, `reject`, or `defer`.
- [x] 1.9 Run `openspec validate omit-empty-evidence-snippets --strict`.
- [x] 1.10 Stop at implementation confirmation gate.

Plan findings:

- `clarify`（internal）：scope is limited to Evidence Pack budget accounting; do not alter grounded answer assembly or `/chat` contract.
- `clarify`（Codex）：mixed ordering should be covered so an empty snippet before a non-empty snippet does not consume budget or prevent later inclusion; added to the RED test plan.
- `clarify`（OpenCode）：evidence id wording could imply use of the budget-assigned `EvidenceItem.snippet`; clarified that stable ids are generated from the original stripped snippet before budget assignment.
- `clarify`（OpenCode）：the in-budget scenario needed an explicit no-empty-snippet precondition for `omitted_count == 0`; clarified in the spec delta.
- `clarify`（OpenCode）：current behavior is inconsistent because empty snippets are included when budget remains but omitted when budget is exhausted; clarified in design context.

Implementation gate:

- User confirmed continuing the code-debt stage in this thread; no additional product decision is open.

## 2. Implementation After Approval

- [x] 2.1 Add RED tests for empty snippet omission and budget accounting.
- [x] 2.2 Add RED tests for whitespace-only snippet omission after normalization.
- [x] 2.3 Preserve existing non-empty include/truncate/omit behavior.
- [x] 2.4 Implement the smallest `build_evidence_pack()` change.
- [x] 2.5 Update durable documentation only for facts that changed.

## 3. Review, Verification, Archive

- [x] 3.1 Run focused `pytest tests/test_evidence_pack.py -q`.
- [x] 3.2 Run adjacent grounded answer / AgentLoop RAG contract tests if needed.
- [x] 3.3 Run `ruff check .`.
- [x] 3.4 Run `openspec validate --all`.
- [x] 3.5 Run `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`.
- [x] 3.6 Run `git diff --check`.
- [x] 3.7 Run final implementation review after the last runtime/test change.
- [x] 3.8 Perform focused Stage Debt Sweep over changed runtime/tests/docs/specs/Harness and directly dependent paths.
- [x] 3.9 Archive the OpenSpec change only after blocking findings are closed and validation passes.

Final implementation review findings:

- `fix`（Codex P3）：final verification / archive gate evidence was not yet backfilled in tasks and checklist; focused, adjacent, ruff, OpenSpec all, full verify, diff check, final review, debt sweep, and archive readiness are now recorded before archive.
- OpenCode final implementation review：no `fix` / `clarify` / `reject` / `defer` findings and no blocking findings.

Validation:

- RED `pytest tests/test_evidence_pack.py -q` before implementation: 3 failed, 4 passed, all failures were old `included=True` empty-snippet behavior.
- GREEN focused `pytest tests/test_evidence_pack.py -q`: 7 passed.
- Adjacent `pytest tests/test_grounded_answer.py tests/test_chat_api.py tests/test_repo_rag.py -q`: 43 passed.
- `ruff check .`: passed.
- `openspec validate --all`: 23 passed, 0 failed.
- `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`: pytest 513 passed, 1 skipped; ruff, stage docs scan, and skill eval structure scan passed.
- `git diff --check`: passed, with CRLF normalization warnings only.

Stage Debt Sweep:

- Inspected changed runtime/tests/docs/OpenSpec/Harness: `app/rag/evidence.py`, `tests/test_evidence_pack.py`, active OpenSpec artifacts, `.harness/allowed_files.md`, `.harness/review_checklist.md`, `docs/PROGRESS.md`, and `HANDOFF_TO_NEXT_CHAT.md`.
- Inspected direct dependencies: `app/answering/grounded_answer.py`, `app/tools/tool_executor.py`, and `app/harness/kernel.py`.
- Result: no new blocking debt. Grounded answer and citation validation already consume only `item.included and item.snippet`; public `/chat` contract, provider runtime, retriever behavior, CI, and network dependencies remain unchanged.

Archive readiness:

- Blocking findings closed; all implementation review findings triaged; focused/adjacent tests, OpenSpec strict/all, ruff, full verify, and `git diff --check` have passed. Ready to archive.
