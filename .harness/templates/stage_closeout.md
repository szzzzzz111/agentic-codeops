# Stage Closeout Template

用于每个阶段 archive 前后更新 `docs/PROGRESS.md`、`HANDOFF_TO_NEXT_CHAT.md` 和 `.harness/*`。只填真实发生的状态，不把下一阶段写成已实现。

## Stage

- Stage: `<Vx stage name>`
- Branch: `<feature branch>`
- Archive path: `openspec/changes/archive/<date-change-name>/`
- Next stage: `<Vy stage name>`

## Completion Summary

- Implemented:
  - `<runtime or docs capability>`
- Preserved boundaries:
  - `<API contract / provider / audit / retrieval / safety boundary>`
- Non-goals still not implemented:
  - `<future capabilities>`

## Verification

- `openspec validate --all`: `<result>`
- `powershell -ExecutionPolicy Bypass -File scripts\verify.ps1`: `<result>`
- `git diff --check`: `<result>`
- `powershell -ExecutionPolicy Bypass -File scripts\check_stage_docs.ps1`: `<result>`

## Review State

- Internal review: `<done / findings>`
- External review: `<done / findings / not requested>`
- Remaining debt:
  - `<record durable debt or "none">`

## Manual Judgment Gates

- `manual_judgment_gates_completed`: `<yes / blockers>`
- Stage intent / scope: `<conclusion>`
- Safety / architecture: `<conclusion>`
- Test adequacy: `<conclusion>`
- Review triage: `<conclusion>`
- Semantic parity: `<conclusion>`
- Archive / merge / handoff truth: `<conclusion>`
- Residual risks / deferred findings: `<durable locations or none>`

## Archive Closeout

- Active change moved to archive.
- Long-term specs synced before archive.
- `openspec list` shows no active changes.
- `README.md`, `docs/PROGRESS.md`, `HANDOFF_TO_NEXT_CHAT.md`, `.harness/allowed_files.md`, and `.harness/review_checklist.md` no longer describe the completed stage as active.
