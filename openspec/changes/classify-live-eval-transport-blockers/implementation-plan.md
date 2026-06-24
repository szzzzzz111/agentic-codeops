# Live Eval Transport Blocker Classification Plan

## Execution Boundary

Allowed implementation surface:

- `evals/live_model_provider/**`
- `tests/test_live_model_provider_eval.py`
- `scripts/run_live_model_eval.ps1`
- `openspec/changes/classify-live-eval-transport-blockers/**`
- `.harness/allowed_files.md`
- `.harness/review_checklist.md`
- `docs/PROGRESS.md`
- `HANDOFF_TO_NEXT_CHAT.md`
- archive sync for `openspec/specs/live-model-provider-eval/spec.md`

Frozen:

- `app/**` runtime behavior
- fixtures/rubric/profile/pricing
- default CI and `scripts/verify.ps1`
- default Patch wiring and `/chat` contract
- historical live evidence files
- V24 planning

## TDD Slices

1. Transport metadata redaction
   - RED: unavailable provider response exposes only allowlisted diagnostic codes in local report.
   - GREEN: evaluator derives `phase`、`error_class`、`status_class` from existing provider audit/metrics fields
     without raw message/url/payload and without modifying `app/**`.

2. Transport blocker outcome
   - RED: all live provider attempts unavailable currently writes evaluated-failure record.
   - GREEN: all-unavailable provider-contact-unverified run returns blocker outcome and writes no tracked evidence.

3. Mixed outcome stays conformance
   - RED/GREEN: if at least one live provider response is available and gates fail, normal conformance failure path remains eligible for evaluated-failure record.

4. Live shell guard
   - RED: runner can start live calls in unconfirmed shell.
   - GREEN: missing explicit live-network confirmation fails closed before provider calls and writes no tracked evidence.

5. Reports and stdout
   - RED/GREEN: stdout/report clearly distinguish PASS、conformance FAIL、SKIP/ERROR、transport blocker.
   - No secret values, URL, prompt, EvidencePack, raw response, exception message, traceback, payload or fingerprint.

## Verification

Focused:

```powershell
pytest tests/test_live_model_provider_eval.py -q
```

Full deterministic:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/verify.ps1
openspec validate classify-live-eval-transport-blockers --strict
openspec validate --all
powershell -ExecutionPolicy Bypass -File scripts/check_stage_docs.ps1
git diff --check
```

No live network run is required to archive this remediation. Any post-remediation provider certification remains a
separate revalidation step.

## Review Targets

- Transport blocker cannot create attestation or evaluated-failure record.
- Conformance FAIL path still works when provider-contact is confirmed.
- Diagnostic metadata is useful but strictly allowlisted and redacted.
- Default verify remains offline.
- Historical evidence is not modified.
- Live-network confirmation guard does not silently bypass user/environment authorization.
