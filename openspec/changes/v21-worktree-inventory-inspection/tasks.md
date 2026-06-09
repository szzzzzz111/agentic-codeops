## 1. Planning And Harness

- [x] 1.1 Create V21 stage planning, proposal, design, tasks, and spec deltas.
- [x] 1.2 Synchronize `.harness/allowed_files.md` and `.harness/review_checklist.md` before runtime edits.
- [x] 1.3 Record V21 as active planning with `passes: false` in durable docs and feature list.
- [x] 1.4 Run internal plan review and `openspec validate v21-worktree-inventory-inspection --strict`.
- [x] 1.5 Obtain explicit implementation confirmation before modifying runtime code or tests.

## 2. TDD: Store, Scope, And Consistency

- [x] 2.1 Add RED tests for latest-20 stable inventory ordering, cross-user/repo isolation, and missing-store no-create behavior.
- [x] 2.2 Add RED tests for metadata, expected directory, Git registry, registry-path, and HEAD/base consistency combinations.
- [x] 2.3 Add RED tests proving unknown or cross-scope ids stop before Git inspection.

## 3. TDD: Git-Derived Data And Safe Preview

- [x] 3.1 Add RED tests proving tracked preview paths come only from `--name-only -z`; user text and metadata changed-files cannot drive per-file diff.
- [x] 3.2 Add RED tests for `--numstat -z` diffstat, streamed hunk count, binary handling, metadata output caps, and Git-error partial results.
- [x] 3.3 Add RED tests proving untracked output exposes count only and never names, prefixes, or content.
- [x] 3.4 Add RED tests for 20-file, 6000-character, 80-lines-per-file, and 300-characters-per-line limits.
- [x] 3.5 Add RED tests for hidden/state/sensitive/binary rejection and absolute-path/DB-path/secret redaction.

## 4. TDD: Routing, Contract, And Audit Skip

- [x] 4.1 Add RED tests for `worktree list` / `列出 worktree` and upgraded status/inspection commands.
- [x] 4.2 Add RED tests proving `worktree_inspection` replaces `worktree_status` and `/chat` top-level fields remain unchanged.
- [x] 4.3 Add RED tests proving inventory / inspection do not call repo RAG, verification, patch, cleanup, or write tools.
- [x] 4.4 Add RED tests proving `_skip_persistent_audit_for_result()` skips both V21 events while preserving safe request-local trace.
- [x] 4.5 Add RED tests proving existing audit row count remains unchanged and missing audit/worktree state remains missing.

## 5. Implementation

- [x] 5.1 Implement read-only scoped inventory in the worktree store and manager.
- [x] 5.2 Implement fixed-argv registry/directory/HEAD consistency inspection, capped machine-readable metadata collection, and streamed hunk counting.
- [x] 5.3 Implement the dedicated streaming bounded safe preview formatter and count-only untracked reporting without unbounded patch capture.
- [x] 5.4 Replace the V20 status route/trace event with V21 inventory/inspection routing and answer formatting.
- [x] 5.5 Extend the unified audit skip predicate for `worktree_inventory` and `worktree_inspection`.

## 6. Docs, Review, And Verification

- [x] 6.1 Update README, ARCHITECTURE, PROGRESS, FEATURE_LIST, HANDOFF, harness, and long-term specs for implemented V21 behavior.
- [x] 6.2 Run V21 targeted tests and relevant AgentLoop/API/audit/V20 regressions.
- [x] 6.3 Run `openspec validate --all`.
- [x] 6.4 Run `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`.
- [x] 6.5 Run `git diff --check`.
- [x] 6.6 Run internal final review and Stage Debt Sweep, including audit-skip traceability evidence.
- [x] 6.7 Stop for expected external review and stage-level confirmation before commit/archive/merge/push.
- [x] 6.8 Review follow-up: bound/redact public metadata and tracked paths, enforce no-write Git/SQLite reads, safely degrade corrupt stores, and always report preview counters.
- [x] 6.9 Record external review completion with no blocking findings and rerun final closeout gates.
