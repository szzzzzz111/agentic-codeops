# Stage Planning Template

用于创建新阶段 OpenSpec change 前的轻量规划。先填这个模板，再写 `proposal.md`、`design.md`、`tasks.md` 和 spec delta。

## Stage

- Stage: `<Vx stage name>`
- Proposed branch: `<feature branch>`
- Capability owner:
  - New capability: `<name or none>`
  - Modified capabilities: `<names>`
- Previous completed stage: `<Vx-1>`

## Intent

- Problem:
  - `<what is missing or unsafe today>`
- Why now:
  - `<why this is the next slice>`
- User-visible outcome:
  - `<what changes for /chat or docs>`

## Scope

- In scope:
  - `<one small vertical slice>`
- Out of scope:
  - `<future stage capability>`
- API contract:
  - `<unchanged / changed with exact fields>`
- Runtime dependency changes:
  - `<none / dependency and reason>`

## Boundaries

- Harness boundaries preserved:
  - `<ToolExecutor / PermissionPolicy / ApprovalGate / provider / audit>`
- Security and audit:
  - `<what must not leak>`
- Retrieval stance:
  - `grep-first, RAG-assisted`; rewrite/rerank must serve lexical/path/symbol baseline.

## Tests

- Unit tests:
  - `<test file and behavior>`
- API / contract tests:
  - `<top-level fields / redaction / fallback>`
- Docs / route-map tests:
  - `<docs assertions>`

## Docs And Harness

- Allowed files to update:
  - `<paths>`
- Review checklist additions:
  - `<gates>`
- Durable docs to update:
  - `README.md`
  - `docs/ARCHITECTURE.md`
  - `docs/PROGRESS.md`
  - `docs/FEATURE_LIST.json`
  - `HANDOFF_TO_NEXT_CHAT.md`

## Human Decisions

- Decision needed:
  - `<stage-level question, not code detail>`
- Default recommendation:
  - `<recommended option>`

## Formal Review Evidence

- Continuous execution authorization:
  - `does not replace formal review, Stage Debt Sweep, validation, or closeout gates`
- Formal code review timing:
  - `after final runtime/tests changes and before archive/merge`
- Required visible conclusion:
  - `<findings ordered by severity / explicit no-findings conclusion with residual risks>`
- Blocking findings:
  - `<none / durable blocker locations>`

## Manual Judgment Gates

- `manual_judgment_gates_planning_completed`: `<yes / blockers>`
- Stage intent / scope:
  - `<goal, non-goals, roadmap order, confirmation boundary>`
- Safety / architecture:
  - `<threat model, fail-closed behavior, permission/tool/ownership boundaries>`
- Test adequacy:
  - `<why planned tests prove requirements, non-goals, error paths, and safety boundaries>`
- Review triage:
  - `<internal plan findings and external feedback classification approach>`
- Semantic parity:
  - `<which durable docs/specs must describe the same planned state>`
- Archive / merge / handoff truth:
  - `<delta operation, long-term spec, branch/remote/handoff risks to review later>`
