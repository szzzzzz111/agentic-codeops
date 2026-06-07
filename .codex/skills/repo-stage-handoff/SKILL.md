---
name: repo-stage-handoff
description: Use when a repo stage is finishing, after merge or push, before switching chats, or when the user asks whether handoff, progress, branch state, or next-step docs are still accurate.
---

# Repo Stage Handoff

## Core Rule

Handoff docs must describe the state a new session will see, not the state that existed while the work was in progress.

## Workflow

1. Check `git status --short --branch`, latest commit, and branch containment when relevant.
2. Read `HANDOFF_TO_NEXT_CHAT.md`, `docs/PROGRESS.md`, `README.md`, `docs/ARCHITECTURE.md`, `docs/FEATURE_LIST.json`, `.harness/allowed_files.md`, and `.harness/review_checklist.md`.
3. Search for stale transition phrases before editing.
4. Run the Stage Debt Sweep before declaring the version done:
   - scan documentation debt first
   - scan code/test debt second
   - fix in-scope debt now, or record remaining debt in `docs/PROGRESS.md` and `HANDOFF_TO_NEXT_CHAT.md`
5. Compare the completed stage's archived OpenSpec proposal/tasks/spec delta with long-term docs; every completed stage must appear consistently in README stage history/current snapshot/roadmap, ARCHITECTURE current chain, PROGRESS, FEATURE_LIST, HANDOFF, and long-term specs when applicable.
6. Update docs to stable wording:
   - current baseline branch
   - active stage or "no active development stage"
   - completed work
   - validation evidence
   - next recommended stage
7. Ensure next-step suggestions do not ask for completed review or completed cleanup, and do not list a completed stage as a future roadmap item.
8. After merge or push, update durable docs again with the actual branch, remote, commit hash, validation evidence, next stage, and branch cleanup/retention decision.
9. Run validation before claiming the handoff is ready.
10. After documentation parity fixes, run full verification, not only a docs grep: tests may encode and enforce stale stage wording.

## Stage Debt Sweep

Every version/stage must end with an explicit debt sweep. Do this before saying the stage is implementation-complete, ready to commit, or archive-ready.

Documentation debt sweep:

- Check current durable docs: `README.md`, `docs/PROGRESS.md`, `docs/ARCHITECTURE.md`, `docs/FEATURE_LIST.json`, `HANDOFF_TO_NEXT_CHAT.md`, `AGENTS.md`, `.harness/allowed_files.md`, `.harness/review_checklist.md`, `openspec/README.md`, `openspec/changes/README.md`, and `openspec/specs/README.md`.
- Check long-term specs under `openspec/specs/**/spec.md`.
- Search for stale prior-stage wording, old branch names, old roadmap order, "current V<N>" references after the stage has advanced, `No specs found`, `暂时保留`, `TBD`, `TODO`, and old route-map phrases.
- Search long-term `openspec/specs/**/spec.md` for archive-generated Purpose placeholders such as `TBD`, `TODO`, and `created by archiving change`; treat any hit in active long-term specs as a blocker before merge, push, archive-ready, or the next stage.
- Run or update `scripts/check_stage_docs.ps1` so the sweep is machine-checkable, not only manually described in chat.
- Check positive parity, not only stale-phrase absence. For a completed user-facing stage, verify README has the capability section, module/path entry when relevant, stage-history section, accurate non-goals, and a roadmap that lists the stage as completed rather than future work.
- Search tests and documentation-check scripts for assertions that lock in the prior stage, old archived marker, old capability list, or stale roadmap wording.
- Treat archive contents as history by default; do not rewrite archive files unless the user explicitly asks or the archive breaks active validation. If archive history is misleading, clarify in current durable docs instead.

Code/test debt sweep:

- Review the stage's changed runtime path plus adjacent older paths it depends on, not only the newly added files.
- Check permissions/tool names, API contract boundaries, path leakage, default constants, routing behavior, error paths, and whether tests have accidentally locked in a bug.
- For every debt item: fix it if it is in scope and low risk; otherwise record it under known remaining code debt in `docs/PROGRESS.md` and `HANDOFF_TO_NEXT_CHAT.md`.
- Do not leave debt only in chat.

## Completed Stage Documentation Parity

When a stage has been implemented, committed, merged, or archived:

- Check `README.md` includes the stage in "当前快照", "当前能力" when user-facing, "阶段历史", "当前非目标", and "路线图" as appropriate.
- Check README current-capability subsections and module inventory include every already-implemented user-facing/runtime component touched by the stage; do not accept a version mention in the snapshot as sufficient parity.
- Check `docs/ARCHITECTURE.md` describes the current runtime chain and does not leave previous-stage wording in the current architecture section.
- Check `docs/PROGRESS.md`, `docs/FEATURE_LIST.json`, and `HANDOFF_TO_NEXT_CHAT.md` include the completed stage, validation evidence, archive path, and next stage.
- After merge/push, check these docs include the actual main/remote state and commit hash, and no longer suggest pending merge/push decisions for the completed stage.
- Avoid self-invalidating hash claims. Record the stable stage runtime/archive merge commit and say later handoff-doc closeout commits entered main/remote history; do not claim current HEAD equals the handoff-doc commit from inside that same uncommitted document update.
- Record whether the completed feature branch is retained or cleaned up. If retained, say whether it is fully merged and points at the same commit as `main`.
- If a new stage has already started, keep both facts true: previous stage completed, current stage active.
- Treat stale long-term docs as a blocker before starting the next implementation stage.
- Run `scripts/check_stage_closeout.ps1` and full `scripts/verify.ps1` after parity/test/checker changes. A docs-only change can still break or expose a stale test.

## Project Defaults

- Current long-term spec entrypoint is `openspec/specs/`.
- Old `specs/00x-*` are retired and must not be reintroduced as the current entrypoint.
- If no active stage exists, `.harness/allowed_files.md` and `.harness/review_checklist.md` should say so and require the next stage to update them first.

## References

Read `references/stale-state-checklist.md` before finalizing a stage or when the user says the handoff/progress docs look possibly stale.
