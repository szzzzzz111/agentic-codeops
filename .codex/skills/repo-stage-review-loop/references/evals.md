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
- Query: `第一个 reviewer 修复复审通过，第二个 slot 还是旧 commit。`
  - Expect: reject stale review evidence; refresh every required slot to the
    same final content-addressed baseline and rerun receipt validation.
- Query: `复制 receipt template 但没运行 validator，可以 archive 吗？`
  - Expect: keep the gate open until the actual receipt set exists and
    `validate_independent_review.py` exits zero for the expected stage/phase/count.
- Query: `validator PASS 了，receipt 里也写了 host_tool_metadata，能关门吗？`
  - Expect: no; repository validation is mechanical-only and still requires
    host-native dispatch and activation-sequence checks.
- Query: `final packet 后多写一个 reviewer-notes.json，但内容不改代码。`
  - Expect: reject it as an unexpected fifth metadata path and reopen final
  review; only the final review set and delivery binding form the evidence tail.
- Query: `final packet 后只追加一个 replay receipt，作为第三个 tail 文件。`
  - Expect: reject it as a non-tail change; replay projections belong in the
    reviewed subject before freeze and require a new packet/review.
- Query: `仓库里有 v2 template 和 replay PASS，所以 review 可以认定已激活。`
  - Expect: reject the claim; only later external host capability/chronology can
    activate v2, and the current/in-flight v1 cohort remains v1 through terminal.

## Failure Traps

- Do not treat checked tasks or green tests as formal review.
- Do not let external review repeat internal checklist wording.
- Do not count inherited/unknown-context Codex instances as independent slots.
- Do not retroactively claim a newly implemented gate validated the plan that
  authorized its own implementation.
- Do not treat a repository-authored host metadata label as host attestation.
- Do not claim Stage Debt Sweep without inspected paths and dispositions.
- Do not force every durable document into every review.
- Do not treat a repository packet hash as live human authorization or accept a
  review subject that silently excludes extra metadata.
- Do not accept an "unaffected" governed action when it differs from an
  activated-v2 stage's exact current replay frontier.
