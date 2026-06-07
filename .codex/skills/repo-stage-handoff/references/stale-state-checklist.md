# Stale State Checklist

## Search Terms

Search handoff/progress/OpenSpec docs for:

- `当前正在`
- `当前工作分支`
- `收尾`
- `review`
- `No specs found`
- `暂时保留`
- old feature branch names after merge
- completed stage names listed as next actions
- `V<N> 规划` or `V<N> will` after that stage is implemented or archived
- previous-stage labels in current architecture, such as `V8 当前` after V9 becomes current
- roadmap bullets that still list the completed stage as future work
- stage history sections missing the most recently completed stage
- current-capability sections or module inventories missing the most recently completed user-facing/runtime capability
- current non-goals that still list an implemented capability as future or forbidden
- tests or docs-check scripts that require an old archived marker, prior-stage capability list, or stale roadmap wording
- post-merge docs that claim current HEAD equals the docs commit being created, causing immediate self-staleness
- stale OpenSpec initialization wording after long-term specs exist
- stale default tool names after runtime tool boundaries change
- stale constants in docs after code defaults change

## Stage Debt Sweep

Before closing any version/stage:

1. Scan documentation debt first.
2. Scan code/test debt second.
3. Fix debt that is in scope.
4. Record remaining debt in durable docs, at minimum `docs/PROGRESS.md` and `HANDOFF_TO_NEXT_CHAT.md`.
5. Re-run validation after fixes.

## Files To Check

- `HANDOFF_TO_NEXT_CHAT.md`
- `docs/PROGRESS.md`
- `README.md`
- `AGENTS.md`
- `docs/ARCHITECTURE.md`
- `docs/FEATURE_LIST.json`
- `openspec/README.md`
- `openspec/specs/**/spec.md`
- `openspec/changes/archive/<completed-stage>/proposal.md`
- `openspec/changes/archive/<completed-stage>/tasks.md`
- `.harness/allowed_files.md`
- `.harness/review_checklist.md`

Check README by responsibility area, not only by version-name presence:

- current snapshot
- current capability sections
- module/path inventory
- stage history
- current non-goals
- roadmap

For code/test debt, also check:

- the stage's changed runtime files
- adjacent older runtime files the stage depends on
- tests that may encode outdated stage names or old behavior
- tests and docs-check scripts that may encode stale documentation state
- long-term specs that describe the touched runtime boundary

## Validation

Minimum checks:

```powershell
openspec validate --all
powershell -ExecutionPolicy Bypass -File scripts/verify.ps1
powershell -ExecutionPolicy Bypass -File scripts/check_stage_closeout.ps1
git diff --check
git status --short --branch
```

If a check cannot run, record why in the final response and in handoff only when it affects future sessions.

## Stable Wording

Prefer:

- `当前基线分支：main`
- `暂无活跃开发阶段`
- `下一阶段开始前，先创建 OpenSpec change`

Avoid:

- `当前正在 feature/...` after merge
- `收尾 V4 review` after review is complete
- `旧 specs 暂时保留` after retirement
- `V9 规划为 ...` after V9 is implemented
- `V8 当前 ...` in the current architecture section after V9 upgrades the chain
- roadmap entries that make a completed stage look unstarted
- exact current-HEAD claims inside an uncommitted post-merge docs update
- `当前阶段仅初始化` after product capabilities have been migrated into long-term specs
- old route-map entries such as `V10 = Query Rewrite / Rerank / Context Budget` after route-map reshuffling
