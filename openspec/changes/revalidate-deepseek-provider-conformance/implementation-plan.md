# DeepSeek Provider Conformance Revalidation Plan

## Execution Boundary

This change performs no runtime or evaluator implementation. Its mutable surface before live execution is limited to:

- `openspec/changes/revalidate-deepseek-provider-conformance/**`
- `.harness/allowed_files.md`
- `.harness/review_checklist.md`

After a PASS live run, it may additionally modify:

- `docs/evals/live-model-provider/<timestamp>.json`
- `docs/PROGRESS.md`
- `HANDOFF_TO_NEXT_CHAT.md`
- `openspec/specs/live-model-provider-eval/spec.md` only through archive sync

After a valid conformance FAIL live run, it may additionally modify only:

- `docs/evals/live-model-provider/failures/<timestamp>.json` when produced by the runner with exclusive-create semantics
- `docs/PROGRESS.md` and `HANDOFF_TO_NEXT_CHAT.md` only to record the pause state

The failure record is pause-site evidence for this revalidation branch only. It is not provider certification evidence and MUST NOT be used to archive, merge to `main`, or push a completed state unless the change contract is formally reshaped first.

The following remain frozen:

- `app/**`
- `evals/**`
- `tests/**`
- `scripts/run_live_model_eval.ps1`
- `scripts/verify.ps1`
- fixtures, rubric, DeepSeek profile and pricing
- default Patch wiring and `/chat` contract

## Pre-Live Sequence

1. Commit reviewed OpenSpec and Harness planning.
2. Run:

   ```powershell
   pytest tests/test_live_model_provider_eval.py -q
   powershell -ExecutionPolicy Bypass -File scripts/verify.ps1
   openspec validate revalidate-deepseek-provider-conformance --strict
   openspec validate --all
   powershell -ExecutionPolicy Bypass -File scripts/check_stage_docs.ps1
   git diff --check
   ```

3. Confirm:
   - tracked worktree is clean;
   - HEAD is the commit to be evaluated;
   - `.env.live` is ignored and contains all five required keys;
   - no values are printed;
   - no manual provider request is sent after this point.
4. Complete internal and independent plan/evidence review.
5. Stop for explicit user confirmation.

## Live Command Contract

Use a single PowerShell process to load `.env.live` into process environment and invoke the runner script. The wrapper MUST:

- read `.env.live`;
- ignore empty lines and `#` comments;
- set only the parsed key/value pairs into the current process environment;
- verify the five required key names are present;
- print only missing key names if validation fails;
- never print values;
- never send an additional provider/model diagnostic request.

After loading the process environment, invoke:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run_live_model_eval.ps1
```

The script/runner contract remains:

- exactly one complete run;
- at most 8 live calls;
- no retry;
- per-call timeout 30 seconds;
- API subprocess timeout 120 seconds;
- whole-run timeout 300 seconds;
- PASS=0, conformance FAIL=1, internal ERROR=2, missing configuration SKIP=0.

## Outcome Handling

### PASS

- Require stdout `PASS live model provider eval` and `attestation=<path>`; exit code 0 alone is insufficient because SKIP also returns 0.
- Require local sanitized report and tracked attestation.
- Require no evaluated-failure record for the same run.
- Verify exact attestation allowlist and report SHA-256.
- Verify 10 planned cases, 8 calls and zero hard-gate failures.
- Verify provider/model/profile/rubric, UTC, latency, complete usage and cost.
- Scan report/attestation for forbidden content.
- Commit attestation and closeout evidence.
- Archive, run `scripts/check_stage_closeout.ps1`, merge and push after final review.
- After archive sync, assert that all six existing long-term requirement headers remain and the new revalidation scenario is present.

### FAIL

- Preserve the runner-produced local report and valid evaluated-failure record.
- Exit code 1 alone is insufficient: require stdout `failure_record=<path>` and an existing valid record before calling it trustworthy conformance evidence.
- Require the failure path to be under `docs/evals/live-model-provider/failures/<timestamp>.json` and produced by the runner's exclusive-create path.
- If exit 1 has no failure-record path, classify it as integrity-blocked/incomplete evidence and keep the change active.
- Do not create or edit an attestation.
- Do not modify runtime/evaluator/tests/profile/rubric.
- The valid failure record may be committed to the current revalidation branch as pause-site evidence, but MUST NOT be archived, merged to `main`, or pushed as a completed state unless the contract is formally reshaped.
- Record the failure and pause this change.
- Any remediation requires a separate OpenSpec change; after remediation, this revalidation evidence becomes stale and the full sequence restarts.

### SKIP / ERROR / Integrity Failure

- Do not treat the run as provider evidence.
- Do not archive.
- Diagnose only after creating or reshaping an appropriate independent change.

## Review Targets

Internal and external review must challenge:

- accidental reuse or overwrite of historical FAIL evidence;
- running against an uncommitted or changing tree;
- hidden retry or extra diagnostic requests;
- PASS attestation generated alongside failure evidence;
- FAIL record misrepresented as certification evidence or completion evidence;
- stale report hash or tested commit;
- certification language broader than recorded commit/profile/rubric;
- secret, prompt, EvidencePack, answer, diff, reasoning or fingerprint leakage;
- default verification acquiring a live-network dependency.
