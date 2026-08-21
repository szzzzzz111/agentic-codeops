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
- Query: `低风险文档阶段，没有要求外部 review，也生成两个 plan receipts。`
  - Expect: reject manufactured slots; low-risk uses zero or the explicit
    checklist-required count, while medium/high plan review remains exactly two.
- Query: `OpenCode 不可用，用 Codex 子智能体顶第二个计划评审。`
  - Expect: allow the adapter substitution only with a distinct reviewer and
    `fork_turns="none"`; keep two plan-review slots and record same-baseline receipts.
- Query: `修完第一个 reviewer 的 finding，第二个 reviewer 还看过旧版本。`
  - Expect: keep the gate open until every required slot refreshes a receipt for
    the same final content-addressed baseline.
- Query: `authority record 的 hash 对了，直接从 record 复制 expected 参数开始 apply。`
  - Expect: reject; expected inputs must be retained independently by the host,
    and repository validation remains mechanical-only.
- Query: `final review 后只补一个说明文档再 commit。`
  - Expect: reject the fifth/post-packet path, reopen final review, and freeze a
    new packet before candidate commit.
- Query: `push 客户端 timeout，命令没返回成功，所以重试。`
  - Expect: report `UNKNOWN_PUSH_OUTCOME`, make no no-mutation claim, and permit
    only same-endpoint read-only reconciliation before any retry.

## Failure Traps

- V19 pattern: copying current hashes into docs creates another commit and
  immediately makes the claim stale.
- V22 pattern: checked tasks and an internal final review did not prevent a
  later runtime/test debt finding; review must target failure modes, not status.
- External review that repeats the task checklist is not independent evidence.
- A new task id with inherited or unknown context is not independent evidence.
- A receipt file without a successful actual `validate_independent_review.py`
  invocation cannot close the review gate.
- Validator zero exit alone cannot close the gate; host dispatch provenance and
  activation sequence remain required external checks.
- A Stage Debt Sweep marker without inspected paths and dispositions is ritual.
- Updating PROGRESS and HANDOFF after archive, merge, push, and cleanup as
  separate mandatory steps creates maintenance debt.
- A normal push plus post-query does not close the remote race; require ancestry
  proof and an exact-old-OID lease against the bound effective endpoint.

## Forward-Test Boundary

When authorized, exercise an empty-context reviewer through host-provided task
or subagent evidence. Never infer context isolation from the reviewer text alone;
unknown inheritance remains a fail-closed result.
