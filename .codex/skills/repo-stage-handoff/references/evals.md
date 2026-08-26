# Repo Stage Handoff Evals

## Positive

- Query: `阶段已经 archive、merge、push，做最终交接。`
  - Expect: verify live state and emit one concise report-only final handoff;
    repository docs were prepared before the final reviewed packet/candidate.
- Query: `准备换会话，只保留下一轮真正需要的信息。`
  - Expect: keep durable history in PROGRESS and current action context in
    HANDOFF.

## Negative

- Query: `帮我实现 audit store。`
  - Expect: use implementation workflow, not handoff.
- Query: `正式 review 这个 patch 生命周期修复。`
  - Expect: use `repo-stage-review-loop`.

## Edge

- Query: `main 和远端一致，把 hash 写进所有文档。`
  - Expect: reject duplicated volatile hashes; reference live Git commands.
- Query: `archive 后发现 runtime bug，顺手在交接里修掉。`
  - Expect: reopen review/archive readiness rather than treating it as docs
    cleanup.
- Query: `candidate commit 后再更新 HANDOFF，随后补一个 docs commit。`
  - Expect: reject the post-candidate repository write; update docs before the
    final packet or reopen review and freeze a new candidate.
- Query: `push timeout 了，但应该没成功，先写已完成交接。`
  - Expect: report `UNKNOWN_PUSH_OUTCOME`, keep `vcs_pushed=unknown`, and permit
    only same-endpoint read-only reconciliation.
- Query: `push 后把 terminal tombstone 和最终 replay receipt 写回仓库。`
  - Expect: reject the post-candidate write; terminal state remains external
    and replay projections belong before final packet freeze.
- Query: `仓库有 replay validator，所以交接写 v2 已激活。`
  - Expect: report replay/v2 dormant unless later external
    `provider_neutral.stage_state_cas/v1` activation is verified; do not infer
    activation from repository bytes.

## Failure Traps

- Do not create separate mandatory handoffs after archive, merge, push, and
  branch cleanup.
- Do not duplicate full stage history in HANDOFF.
- Do not claim exact current HEAD from inside a change that will create a newer
  commit.
- Do not start the next stage during closeout.
- Do not let final handoff create a commit after the host-retained exact
  candidate or infer human authorization/push success from repository receipts.
- Do not add a third replay evidence-tail file or reinterpret an in-flight v1
  stage as v2 during handoff.
