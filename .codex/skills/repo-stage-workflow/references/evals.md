# Repo Stage Workflow Evals

These cases are the RED baseline and forward routing checks for this skill.

## Positive

- Query: `按现有流程把这个阶段一路做到 archive、merge 和 push。`
  - Expect: load this skill; preserve TDD, final review, verification, archive,
    and one post-push handoff without repeated confirmation prompts.
- Query: `这个阶段会改 Git subprocess、SQLite 状态和 patch 生命周期。`
  - Expect: classify as high risk and require independent adversarial review.

## Negative

- Query: `解释一下 /chat 的调用链。`
  - Expect: do not load this skill; this is architecture comprehension.
- Query: `OpenCode 给了两个 finding，帮我判断对不对。`
  - Expect: use `external-review-triage`; do not restart the whole stage.

## Edge

- Query: `tasks 和 tests 都过了，但正式 review 后又改了 runtime。`
  - Expect: invalidate stale review evidence and rerun affected verification
    plus formal review before archive.
- Query: `已经 archive 了，刚发现一个必须改的运行时 bug。`
  - Expect: do not hide it in handoff; reopen review/archive readiness.
- Query: `只是改开发流程文档和本地 skill。`
  - Expect: low-risk process-only stage; no runtime tests or external review
    unless requested, but deterministic validation still applies.

## Failure Traps

- V19 pattern: copying current hashes into docs creates another commit and
  immediately makes the claim stale.
- V22 pattern: checked tasks and an internal final review did not prevent a
  later runtime/test debt finding; review must target failure modes, not status.
- External review that repeats the task checklist is not independent evidence.
- A Stage Debt Sweep marker without inspected paths and dispositions is ritual.
- Updating PROGRESS and HANDOFF after archive, merge, push, and cleanup as
  separate mandatory steps creates maintenance debt.

## Forward-Test Limitation

Model-level subagent routing was not run because this session did not have user
authorization to spawn subagents. Structural checks and these historical
failure cases are the available deterministic evidence.
