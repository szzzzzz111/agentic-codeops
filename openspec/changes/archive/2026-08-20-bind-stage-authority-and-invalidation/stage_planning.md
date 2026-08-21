# Stage Planning

## Stage

- Name: `bind-stage-authority-and-invalidation`
- Branch/worktree: `codex/bind-stage-authority-and-invalidation` / isolated worktree
- Risk: `high` / Human Review Depth `L3`
- Risk reason: changes the development workflow's human authorization and Git closeout failure semantics
- Previous baseline: `origin/main` at the live stage-start commit

## Intent And Scope

- Problem: continuous authorization is not mechanically bound to one exact stage, risk, action ceiling, and Git target.
- Outcome: an append-only authority envelope and separate delivery binding can be checked against the real Git change set, actual review set, exact candidate HEAD, and exact push target, while live direct-user authority remains an external host fact.
- In scope: authority/delivery templates, deterministic validator, scope/epoch invalidation, exact-old-OID push and reconciliation rules, all supported apply/archive workflow entrypoints, tests, and stage evidence.
- Non-goals: runtime Git automation, runtime human identity, cryptographic signatures, hosted approval UI, background execution, connector/MCP/subagent product capability, PR creation, non-fast-forward update, rebase, or history rewrite.
- Public/runtime contract: unchanged; process-only development workflow change.

## Boundaries And Failures

- Owned modules/state: repo-local workflow files, `.harness/authority/**`, templates, validator, tests, and OpenSpec artifacts.
- Trust boundaries: the host's direct-user interaction is authority; repository JSON is only a mechanical binding; Git commands are live VCS evidence.
- Failure behavior: missing external authority, stale/forked epoch, real changed-path escape, scope/risk/action/target drift, stale remote tip, review-manifest mismatch, exact-candidate mismatch, subprocess timeout/output/prompt, or cleanup failure fails closed at the affected action gate; ambiguous push stays `unknown`.
- Audit/privacy implications: store a host reference and bounded stage facts, never user message content, credentials, tokens, or a claim of machine-proven identity.

## TDD And Verification

- First RED cases: forged/self-authored authority cannot yield `human_authorized=true`; scope/risk/action/remote/branch/base/reviewed-HEAD drift fails; fast-forward preflight and post-push verification have positive cases.
- Positive/negative/safety cases: canonical hash, action ordering, unique linear epoch head, committed/staged/unstaged/untracked/rename/delete scope closure, Git ancestry, effective fetch/push endpoints, exact candidate merge, closed review-metadata set, review-set/manifest binding, exact lease race, bounded noninteractive subprocess, ambiguous-outcome recovery, malformed/extra fields, symlink/path constraints, and cleanup failure.
- Focused verification: `pytest tests/test_stage_authority_validation.py -q`; workflow structural tests; changed Python Ruff.
- Full verification trigger: validator/tests change, therefore run repository verification when available and record baseline debt honestly.

## Review Plan

- Internal review target: authority provenance claim ceiling, invalidation completeness, Git race windows, self-bootstrap activation, and workflow/runtime separation.
- External review: two independent empty-context plan slots; high-risk final implementation review per risk contract.
- Independent counterexamples requested: internally consistent forged receipt, real diff outside record scope, stale/forked epoch, target substitution/pushurl, review receipt self-reference, archive/merge bypass, remote-tip TOCTOU, and false/ambiguous `push succeeded` conclusion.
- Stage Debt Sweep paths: changed workflow/tests/scripts/templates/specs plus current independent-review gate and Git closeout rules.

## Files And Durable Facts

- Allowed files: synchronized in `.harness/allowed_files.md`.
- Review checklist additions: L3 human gate, two independent plan slots, authority claim ceiling, invalidation matrix, pre-push and post-push evidence.
- Durable docs whose owned facts change: `docs/AGENT_RULES.md`, long-term workflow specs, `docs/PROGRESS.md`, and final `HANDOFF_TO_NEXT_CHAT.md` only when those facts become true.
- Facts intentionally queried live: branch, HEAD, remote URL, remote target tip, active OpenSpec change, and post-push remote state.

## Human Confirmation

- Internal plan review: completed; both blind empty-context slots have no remaining findings on the current plan, while host provenance remains external to repository proof.
- Decision: direct-user `补` renewed the earlier `push吧` authorization on 2026-08-20 for the corrected envelope including the exact archive output path; later envelope drift still invalidates it.
- Recommendation: implement the lightweight repository binding plus live-host/live-Git gates; do not copy the Greenfield control plane.
- Implementation starts only after: the final status packet refresh, plan receipt mechanical check, and immutable epoch-1 binding are complete.
