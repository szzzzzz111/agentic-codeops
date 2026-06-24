# Implementation Plan

## Stage contract

- Change: `harden-grounded-prompt-injection-live-behavior`
- Risk: `high`
- Parent context: paused `revalidate-deepseek-provider-conformance` has a trustworthy conformance FAIL with only
  `prompt_injection_executed`.
- Goal: harden grounded-text prompt behavior so repository evidence instructions remain data and do not get executed.

## Frozen scope

- Do not modify `evals/**`, live fixture/rubric/profile/pricing, evidence records, `scripts/run_live_model_eval.ps1`,
  `scripts/verify.ps1`, default CI, `/chat` public contract, default Patch wiring, or V24 planning.
- Do not run live gate in this remediation.
- Do not use output cleaning, marker blacklist, evidence filtering/projection, extra model calls, retry, or model switch.
- Do not rewrite or delete existing PASS/FAIL evidence.

## Writable scope

- `app/providers/model_provider.py`
- `tests/test_model_provider.py`
- Adjacent tests only if directly required: `tests/test_grounded_answer.py`, `tests/test_chat_api.py`
- `openspec/changes/harden-grounded-prompt-injection-live-behavior/**`
- `.harness/allowed_files.md`
- `.harness/review_checklist.md`
- `docs/PROGRESS.md`
- `HANDOFF_TO_NEXT_CHAT.md`

## TDD plan

1. RED: add tests that inspect the actual OpenAI-compatible HTTP payload:
   - grounded-text prompt explicitly says to answer by extracting repository facts from evidence data;
   - directed-at-assistant evidence instructions and their requested output target are to be ignored;
   - hostile raw evidence remains present in the user message;
   - the attack target is not copied into the system prompt as a marker-specific blacklist;
   - same-string repository identifier exception remains present;
   - `json_object` mode stays unchanged.
2. GREEN: minimally edit grounded-text prompt construction.
3. REFACTOR: keep wording compact, remove duplicated assertions, and preserve existing tests.

## Verification plan

Pre-implementation planning:

```powershell
openspec validate harden-grounded-prompt-injection-live-behavior --strict
openspec validate --all
powershell -ExecutionPolicy Bypass -File scripts/check_stage_docs.ps1
git diff --check
```

Implementation:

```powershell
pytest tests/test_model_provider.py -q
powershell -ExecutionPolicy Bypass -File scripts/verify.ps1
openspec validate harden-grounded-prompt-injection-live-behavior --strict
openspec validate --all
powershell -ExecutionPolicy Bypass -File scripts/check_stage_docs.ps1
git diff --check
```

## Review plan

- Internal review: prompt contract, no-filter/no-sanitizer boundary, citation footer preservation, JSON mode isolation,
  paused revalidation evidence semantics.
- Independent adversarial review: prompt-injection bypass, marker-blacklist regression, over-constraint of legitimate
  prompt-like repository facts, hidden evaluator/gate weakening, default network isolation.
- Stage Debt Sweep: changed provider prompt/test paths plus direct grounded-answer citation fallback dependencies.

## Revalidation handoff

After archive and merge back to `codex/revalidate-deepseek-provider-conformance`, the previous live FAIL evidence
becomes stale for certification because runtime prompt changed. A renewed DeepSeek live gate requires explicit user
confirmation, a clean tracked tree, no retry, no model switch, and the existing revalidation live execution contract.
