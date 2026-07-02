## Why

`app/rag/evidence.py` currently treats an empty or whitespace-only retrieval
snippet as `included=True` while consuming `0` context budget. Real retrievers
normally return non-empty chunks, but this edge case makes audit summaries less
truthful: an item with no answerable evidence can count as included evidence.

This stage closes that small RAG debt by making empty snippets explicit omitted
evidence. It keeps the Evidence Pack item for auditability, but prevents empty
content from contributing to `included_count` or grounded answer eligibility.

## What Changes

- Treat empty or whitespace-only snippets as not included in the context budget.
- Keep the evidence item with `snippet=""`, `included=False`, and
  `truncated=False`.
- Increment `omitted_count` for empty snippets without consuming budget.
- Preserve stable item ordering, stable evidence ids, absolute-path rejection,
  truncation behavior for non-empty snippets, audit summary keys, and `/chat`
  public contract.
- Add focused RED tests for empty and whitespace-only snippets.
- Update only durable docs whose owned facts changed.

Non-goals:

- Do not change retrieval, chunking, scoring, query understanding, rewrite,
  rerank, grounded answer prompt assembly, provider runtime, or citation
  validation.
- Do not add new `/chat` fields, public API behavior, external dependencies,
  network calls, or provider API key requirements.
- Do not change hybrid fusion weights, capability-status parsing, or historical
  test naming debt.

## Capabilities

### Modified Capabilities

- `repo-query-understanding-rag`

## Impact

- Code:
  - `app/rag/evidence.py`
- Tests:
  - `tests/test_evidence_pack.py`
- Docs:
  - `.harness/allowed_files.md`
  - `.harness/review_checklist.md`
  - `docs/PROGRESS.md`
  - `HANDOFF_TO_NEXT_CHAT.md`
  - `openspec/specs/repo-query-understanding-rag/spec.md` at archive time
