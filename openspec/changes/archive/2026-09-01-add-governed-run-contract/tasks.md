## 1. Freeze And Review

- [x] 1.1 Reconcile live `origin/main`, verify exact endpoint/tip, and create an isolated clean worktree from
  `cf2679b9fc96e54cfb7a665ff7c0a4aaf05b9dd0` without writing the original dirty worktree.
- [x] 1.2 Freeze high/L3 authority, exact allowed paths, decision semantics, claim ceiling, non-goals and stop conditions.
- [x] 1.3 Bind two empty-context independent plan-review slots to one frozen packet and clear all P0/P1 findings.
- [x] 1.4 Pass OpenSpec strict, plan review-set and implement authority preflight, then obtain the user's L3 implementation
  confirmation for the complete design/tasks/spec decisions.

## 2. RED Tests

- [x] 2.1 Add failing contract tests for dirty/inconsistent baseline, unsafe or duplicate allowed tracked paths,
  non-whitelisted/resolved-command drift, direct constructors and `dataclasses.replace` invariant bypass.
- [x] 2.2 Add failing Codex adapter tests for run/thread identity, open prefix, exact completion, missing closed terminal/claim,
  failed terminal, ready-then-failed, duplicate/ambiguous chronology and claim snapshot binding.
- [x] 2.3 Add failing Git collector tests for staged/unstaged/rename paths, masked staged index blobs, ordinary+ignored untracked inventory,
  non-repository/root mismatch, input/tracked symlink, gitlink, malformed NUL output, inherited `GIT_*`, malicious
  fsmonitor/textconv/local+worktree-scope clean/process filter, submodule preflight ordering, fixed argv/env/stdin,
  trusted Git executable resolution, raw bytes/mode normalization gaps, unsupported-platform pre-spawn failure,
  timeout/output cap/process cleanup, observable two-sample drift, unobservable ABA claim ceiling and no repository mutation.
- [x] 2.4 Add failing evaluator tests for out-of-scope/all-untracked paths, zero-change ready claim, repository/HEAD drift,
  cross-run/thread/claim/receipt replay, premature receipt, event invalidity, verification missing/failed, resolved-command
  mismatch, receipt/post-snapshot drift, deterministic precedence and a total claim × change × receipt decision matrix.
- [x] 2.5 Add claim-ceiling and archived-real-observation shape regression tests proving every outcome keeps
  `task_complete/product_acceptance/git_delivery_authorized=false`, provenance unverified, continuity limited to stable endpoint
  samples, and synthetic/archive fixtures never become current-run real-source evidence.

## 3. Minimal Kernel

- [x] 3.1 Implement immutable supervision contracts, controlled factories, defensive validation, run/thread/claim/command
  correlation and canonical snapshot/result hashing.
- [x] 3.2 Implement the pure Codex JSON event adapter with explicit `stream_closed` semantics and stable reason codes.
- [x] 3.3 Implement the child-env-allowlisted, no-helper, fixed-argv, `shell=False`, `GIT_OPTIONAL_LOCKS=0` Git snapshot
  collector with timeout/output caps, process cleanup, all-untracked inventory, two stable samples and bounded errors.
- [x] 3.4 Implement the pure governed-run evaluator with conflict-first exhaustive precedence, stable reason codes and no
  runtime/public orchestration.
- [x] 3.5 Make all focused RED tests GREEN without modifying `/chat`, CLI, ToolRegistry, provider defaults or existing
  patch/worktree/verification behavior.

## 4. Verify And Review

- [x] 4.1 Update architecture, feature and progress documents with the exact internal capability, boundaries and unknowns.
- [x] 4.2 Run focused tests, qualification regression, changed-file Ruff, `git diff --check`, OpenSpec strict and canonical
  `python3 -I scripts/verify.py`.
- [x] 4.3 Freeze the final implementation packet, complete two isolated implementation-review slots, clear all P0/P1
  findings, and rerun affected gates after any packet-affecting fix.
- [x] 4.4 Report exact evidence and remaining unknowns while leaving the change unarchived, uncommitted, unmerged and
  unpushed.
