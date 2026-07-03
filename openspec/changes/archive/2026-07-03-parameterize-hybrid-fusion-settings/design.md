## Context

Hybrid fusion is the deterministic "mixing recipe" that combines lexical
retrieval scores and embedding retrieval scores. Today the recipe is split
across `hybrid_fuse()` default arguments and `DEFAULT_MIN_FUSED_SCORE`.
`HybridRepoRetriever.last_channel_summary` records the minimum score, but not
the lexical/embedding weight pair.

The current defaults are intentionally grep-first: lexical evidence keeps more
influence than embedding evidence. This change makes that recipe explicit while
preserving the same defaults.

## Risk

Risk level: `medium`.

Reason: this is localized runtime behavior in repo-local RAG retrieval. It does
not write files, mutate repositories, touch subprocesses, change public `/chat`
schema, call providers, or add network dependencies, but it sits on ranking
behavior and can affect retrieval order if custom settings are used.

## Target Behavior

`repo_rag.py` shall:

- define an immutable `HybridFusionSettings` value with `lexical_weight`,
  `embedding_weight`, and `min_fused_score`;
- expose default settings whose values match current defaults:
  `lexical_weight=0.65`, `embedding_weight=0.35`, and
  `min_fused_score=0.35`;
- validate settings at construction time: weights must be finite,
  non-negative numbers and at least one weight must be positive;
- validate `min_fused_score` at construction time as finite and non-negative;
- allow `HybridRepoRetriever` to receive settings through dependency injection;
- make `hybrid_fuse()` use settings as the single source for weight and
  threshold calculations;
- keep `max_results` as a per-call result cap, not a settings field;
- make `settings` the single source of truth when it is provided to
  `hybrid_fuse()`; standalone compatibility keyword values are used only when
  `settings` is omitted, and are resolved into settings before scoring;
- record effective `lexical_weight`, `embedding_weight`, and `min_fused_score`
  in `last_channel_summary`;
- preserve those effective settings when `ToolExecutor` aggregates channel
  summaries across rewrite variants;
- preserve default retrieval ordering, lexical anchor filtering, deduplication,
  and `max_results` behavior.

## Public And Audit Boundaries

- `/chat` top-level fields remain unchanged: `trace_id`, `answer`,
  `related_files`, and `tool_calls`.
- `ToolExecutionResult.call_summary()` must not expose the settings.
- Effective settings may appear only in internal audit/trace summary using
  safe scalar values. In the `/chat` path, `ToolExecutor.audit_summary` must
  preserve those values for internal trace/audit, while `call_summary()` keeps
  the public tool-call summary unchanged.
- No path, prompt, Evidence Pack body, provider content, API key, or external
  payload is introduced.

## Non-Goals

- No changes to query understanding, chunk generation, lexical scoring,
  embedding vector math, query rewrite, rerank, Evidence Pack, grounded answer,
  provider runtime, live eval, default CI, or network dependencies.
- No public runtime configuration surface, CLI option, environment variable, or
  `/chat` parameter for tuning fusion settings.
- No broad cleanup of capability-status parsing, assistant status parser, or
  historical test names.

## Test Plan

- RED test: default settings preserve current `hybrid_fuse()` scores and order.
- RED test: custom settings can deterministically change whether a result
  passes the threshold or how lexical/embedding scores are mixed.
- RED test: invalid settings fail fast for negative, non-finite, or all-zero
  weights.
- RED test: `HybridRepoRetriever.last_channel_summary` records effective
  lexical weight, embedding weight, and minimum fused score.
- RED test: `ToolExecutor.search_repo_rag()` preserves effective settings in
  internal audit summary but `ToolExecutionResult.call_summary()` does not
  expose them.
- Regression: lexical anchor behavior for symbol/path queries remains
  unchanged.
- Regression: `ToolExecutionResult.call_summary()` and `/chat` public contract
  remain unchanged.
- Verification:
  - focused `pytest tests/test_repo_rag.py -q`;
  - adjacent `pytest tests/test_agent_harness_kernel.py tests/test_chat_api.py -q`
    if final review requires public contract coverage;
  - `ruff check .`;
  - `openspec validate --all`;
  - `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`;
  - `git diff --check`.

## Review Plan

Because this is medium risk, complete before implementation:

- internal plan review;
- Codex independent plan review;
- OpenCode independent plan review, first running `opencode session list` and
  then reusing an existing review session when available.

All plan and implementation findings must be classified as `fix`, `clarify`,
`reject`, or `defer`.
