## Risk

Risk level: `medium`.

Reason: the intended behavior is cleanup-only, but the touched path is front-of-loop
routing in `AgentLoop` / `RequestRouter`. A regression could route status or repo
search requests incorrectly while keeping the public `/chat` schema unchanged.

## Current Behavior

- `RequestRouter.route()` calls `_asks_about_unimplemented_vector_stack()` directly.
- `_asks_about_unimplemented_vector_stack()` mixes capability vocabulary, search
  disambiguation, and status-question terms in one inline helper.
- `_capability_status_answer()` independently re-parses the message to choose the
  existing capability answer.
- `is_assistant_status_request()` is already intentionally narrow and rejects
  Memory / Long Task prefixes before matching explicit status phrases.
- Several tests still encode historical stage labels in names even when the behavior
  under test is stable capability routing.

## Target Behavior

- Add an internal capability-status classifier helper that owns the existing
  routing-level detection rules and returns a deterministic classification for
  capability-status questions. This extraction applies to the current
  `_asks_about_unimplemented_vector_stack()` routing check only; answer selection
  in `_capability_status_answer()` and `_asks_about_unimplemented_v10_stack()`
  remains behaviorally unchanged.
- `RequestRouter.route()` uses the classifier result. Existing route output remains:
  `route="capability_status"`, `keyword="capability_status"`, and
  `reason="capability_status_question"`.
- The classifier remains inside `RequestRouter`; it MUST NOT be hoisted before
  AgentLoop pre-router routes such as worktree, patch, verification, audit recovery,
  Memory, Long Task, or Assistant Control Surface.
- `_capability_status_answer()` continues to produce the same answer strings for
  existing covered questions.
- Assistant Control Surface status parsing remains strict. This change does not add
  new status trigger phrases or natural-language variants.
- Test names become capability-oriented where practical, without deleting historical
  assertion content that documents archived behavior. Renamed tests must preserve
  their existing route and answer assertions.

## Non-Goals

- Do not add broader natural-language support for status questions.
- Do not change answer text except if tests reveal unavoidable punctuation or helper
  naming issues; such text changes should be rejected unless explicitly needed.
- Do not modify `/chat` public response schema.
- Do not touch Memory, Long Task, Patch, Verification, Audit, Worktree, provider,
  Evidence Pack, RAG retrieval, or live eval runtime.

## Data Returned And Not Returned

No public data changes. The classifier is internal only. `/chat` responses still use
the existing `answer`, `related_files`, and `tool_calls` fields plus `trace_id` at
the API layer.

## Error Behavior

No new error state. Unknown or non-capability questions continue to fall through to
repo search or chat-only behavior using the existing `RequestRouter` rules.

## Security And Routing Boundaries

- Capability-status questions must not call `repo_rag`.
- Search-like questions containing location terms such as `where`, `locate`, `哪里`,
  `在哪`, or `定位` must not be swallowed by capability-status classification.
- Memory and Long Task commands containing status words must continue to outrank
  Assistant Control Surface status parsing.

## Trace And Audit

No new trace fields. Existing `request_routed` summaries for capability-status
questions remain route-based and do not expose internal classifier detail.

## Review Plan

Medium risk requires internal plan review, Codex independent plan review, and
OpenCode independent plan review before implementation. Final implementation review
must run after the last runtime/test change.
