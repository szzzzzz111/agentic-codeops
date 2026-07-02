## Context

Evidence Pack budget accounting is the boundary between retrieval results and
grounded answer eligibility. Current behavior calls `.strip()` on
`line_text`, then includes the item whenever `remaining > 0` and
`len(original_snippet) <= remaining`. For an empty string this marks the item as
included and increments `included_count`, while `budget_used_chars` remains
unchanged. The same empty snippet is omitted when `remaining == 0`, so the
current behavior is also inconsistent across budget states.

## Risk

Risk level: `medium`.

Reason: this is localized runtime behavior in the RAG evidence boundary. It
does not write files, mutate repositories, touch subprocesses, change public
`/chat` schema, or affect provider configuration, but it can change whether an
edge-case retrieval result is considered answerable evidence.

## Target Behavior

`build_evidence_pack()` shall:

- continue rejecting absolute `file_path` values;
- coerce line and score metadata exactly as today;
- normalize snippets with the existing `.strip()` behavior;
- treat `snippet == ""` after normalization as omitted evidence;
- keep the item in `EvidencePack.items` with `snippet=""`, `included=False`,
  and `truncated=False`;
- increment `omitted_count` for each empty snippet;
- not consume context budget for empty snippets;
- continue stable evidence id generation from the original stripped snippet,
  before the budget-assigned snippet is finalized;
- preserve all existing truncation and omission semantics for non-empty snippets.

Grounded answer behavior should improve as a consequence of the existing
contract: if all retrieval items are empty snippets, the Evidence Pack has no
`included=True` items and the grounded answer path should use the existing
no-evidence fallback rather than treating empty content as answerable.

## Non-Goals

- No changes to retriever output, chunk construction, lexical/embedding scoring,
  hybrid fusion, query rewrite, rerank, or citation validation.
- No changes to `GroundedAnswerGenerator`, `ModelProvider`, `ToolExecutor`,
  `AgentLoop`, persistent audit schema, public `/chat` response shape, provider
  runtime, live eval, default CI, or network dependencies.
- No broad cleanup of capability-status parsing, hybrid fusion constants, or
  historical test names.

## Test Plan

- RED test: an empty `line_text` result remains an evidence item but is
  `included=False`, `truncated=False`, increments `omitted_count`, and leaves
  budget used at `0`.
- RED test: whitespace-only `line_text` behaves the same after normalization.
- RED test: an empty snippet before a non-empty snippet does not consume budget
  or prevent the later non-empty item from being included.
- Regression: existing include/truncate/omit behavior for non-empty snippets
  remains unchanged.
- Regression: audit summary fixed keys and `/chat.tool_calls` Evidence Pack
  exclusion remain unchanged.
- Verification:
  - focused `pytest tests/test_evidence_pack.py -q`;
  - adjacent grounded answer / AgentLoop RAG contract tests if needed;
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
