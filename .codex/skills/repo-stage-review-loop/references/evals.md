# Repo Stage Review Loop Evals

Use these as routing and behavior checks after changing the skill.

## Positive

- Query: `外部 review 给了三个 P2，核对后修掉。`
  - Expect: load this skill, usually with external-review-triage; verify each finding against repo reality.
- Query: `实现完成了，最终 review 一遍，没问题就归档。`
  - Expect: load this skill; enforce stop gates, Stage Debt Sweep, delta operation audit, docs parity, and full verification.

## Negative

- Query: `按已经确认的计划继续实现。`
  - Expect: do not make review-loop the primary workflow unless a review checkpoint or failure is reached.
- Query: `现在几点？`
  - Expect: do not load this skill.

## Edge

- Query: `openspec validate 通过了，可以 archive 吗？`
  - Expect: load this skill; also verify tasks, review evidence, long-term Purpose, and delta `ADDED/MODIFIED/REMOVED` header alignment.
- Query: `README 提到了 V19，文档应该同步了吧？`
  - Expect: load this skill; check snapshot, capability section, module inventory, stage history, non-goals, roadmap, and stale tests.

## Failure Traps

- A passing OpenSpec validation does not prove archive sync can apply delta operations.
- A docs test may encode stale prior-stage wording and fail only after the correct docs fix.
- Do not call a stage complete while final review or Stage Debt Sweep tasks predate the final changes.
