## Why

`app/rag/repo_rag.py` currently keeps hybrid fusion tuning values in scattered
function defaults: lexical weight `0.65`, embedding weight `0.35`, and
`DEFAULT_MIN_FUSED_SCORE = 0.35`. These defaults work today, but they make the
retrieval contract harder to audit because the "mixing recipe" is not a single
named value.

This stage closes that small RAG debt by introducing an explicit deterministic
hybrid fusion settings object. Default behavior stays unchanged: grep-first,
RAG-assisted retrieval remains the baseline, no external vector service is
introduced, and `/chat` public response shape is not changed.

## What Changes

- Add a small immutable settings object for hybrid fusion weights and minimum
  fused score.
- Make `HybridRepoRetriever` accept those settings and pass them into
  `hybrid_fuse()`.
- Keep the existing default lexical/embedding weights and minimum fused score.
- Record the effective settings in internal channel audit summary so the
  retriever and `ToolExecutor` audit path can explain which deterministic
  recipe was used.
- Preserve lexical anchor behavior for symbol/path queries, stable ordering,
  deduplication, `max_results`, and public `/chat` contract.
- Add focused RED tests for default behavior, custom settings, validation, and
  audit summary.

Non-goals:

- Do not change query understanding, chunking, lexical scoring, embedding
  vector generation, query rewrite, rerank, Evidence Pack, grounded answer,
  provider runtime, live eval, default CI, or network dependencies.
- Do not introduce external configuration files, environment variables, user
  commands, public `/chat` fields, or runtime tuning APIs.
- Do not change actual default ranking results except where tests explicitly
  use custom in-process settings.

## Capabilities

### Modified Capabilities

- `repo-query-understanding-rag`

## Impact

- Code:
  - `app/rag/repo_rag.py`
  - `app/tools/tool_executor.py`
- Tests:
  - `tests/test_repo_rag.py`
  - `tests/test_tool_executor.py`
- Docs:
  - `.harness/allowed_files.md`
  - `.harness/review_checklist.md`
  - `docs/PROGRESS.md`
  - `HANDOFF_TO_NEXT_CHAT.md`
  - `openspec/specs/repo-query-understanding-rag/spec.md` at archive time
