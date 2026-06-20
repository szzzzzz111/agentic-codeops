# Repo Stage Review Loop Evals

## Positive

- Query: `实现完成了，按最终代码做正式 review。`
  - Expect: inspect contract, diff, tests, failure modes, and dependent paths;
    report findings or an explicit no-findings conclusion with residual risk.
- Query: `review 后又改了 runtime，现在能 archive 吗？`
  - Expect: reject stale evidence and rerun verification plus formal review.

## Negative

- Query: `按已确认计划继续实现。`
  - Expect: implementation skill is primary until a review checkpoint.
- Query: `已经 push，整理下一轮交接。`
  - Expect: use `repo-stage-handoff`.

## Edge

- Query: `OpenSpec 和 tests 都通过了，可以 archive 吗？`
  - Expect: still inspect final review freshness, findings, delta operations,
    and focused debt evidence.
- Query: `外部 reviewer 说应该全面重构。`
  - Expect: verify evidence and classify; reject or defer scope expansion.

## Failure Traps

- Do not treat checked tasks or green tests as formal review.
- Do not let external review repeat internal checklist wording.
- Do not claim Stage Debt Sweep without inspected paths and dispositions.
- Do not force every durable document into every review.
