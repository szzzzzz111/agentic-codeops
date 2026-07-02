# 交接给下一轮 Chat

## 当前基线

- 当前分支：`codex/omit-empty-evidence-snippets`。
- Active OpenSpec change：无。
- 最近归档 OpenSpec change：`omit-empty-evidence-snippets`，归档到
  `openspec/changes/archive/2026-07-02-omit-empty-evidence-snippets/`。
- 当前阶段风险级别：medium。
- 当前阶段目标：修复 `app/rag/evidence.py::build_evidence_pack()` 对 empty /
  whitespace-only snippet 的 Context Budget 计数语义。

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
- `openspec validate omit-empty-evidence-snippets --strict` 已通过。
- TDD RED 已完成：empty snippet、whitespace-only snippet、empty-before-non-empty mixed
  ordering 3 个新增测试在旧实现下按预期失败。
- GREEN 实现已完成：empty / whitespace-only snippet 保留 evidence item 以便审计，但
  `included=False`、`truncated=False`、不消耗 budget，并计入 `omitted_count`；后续非空
  item 仍可正常纳入预算。

## 当前验证

- RED：`pytest tests/test_evidence_pack.py -q` 曾出现 3 failed、4 passed，失败点均为旧实现把
  empty snippet 标成 `included=True`。
- GREEN：`pytest tests/test_evidence_pack.py -q`：7 passed。
- Adjacent：`pytest tests/test_grounded_answer.py tests/test_chat_api.py tests/test_repo_rag.py -q`：
  43 passed。
- `ruff check .`：passed。
- `openspec validate --all`：23 passed，0 failed。
- `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`：pytest 513 passed，1 skipped；
  ruff、stage docs scan、skill eval structure scan passed。
- `git diff --check`：passed，仅 CRLF normalization warnings。

## 下一步

- Final implementation review 和 focused Stage Debt Sweep 已完成，findings 已按
  `fix / clarify / reject / defer` 记录到 `.harness/review_checklist.md`。
- OpenSpec archive 已完成，长期 `repo-query-understanding-rag` spec 已同步；archive 后
  `openspec list` 为 No active changes found，`openspec validate --all` 为 22 passed、0 failed。
- Archive-after full `scripts/verify.ps1` 已通过，pytest 513 passed、1 skipped；archive-after
  `git diff --check` 已通过，仅 CRLF normalization warnings。
- 下一步是 commit/merge/push closeout。

## 剩余债

- 本阶段已处理 `app/rag/evidence.py` empty snippet included-count 债务。
- 其他长期剩余债仍以 `docs/PROGRESS.md` 的“已知剩余代码债”为准。
